import uuid
import tempfile
import os
from typing import List
import pypdf
from groq import Groq
from bucket_manager import get_collection, add_document_meta, delete_document_meta, list_documents
from config import GROQ_API_KEY, GROQ_MODEL, TOP_K_RESULTS, MAX_CHUNK_WORDS, CHUNK_OVERLAP


# ── Groq client ───────────────────────────────────────
def get_groq_client():
    return Groq(api_key=GROQ_API_KEY)


# ── PDF Processing ────────────────────────────────────

def extract_chunks_from_pdf(file_path: str) -> List[dict]:
    """Extract overlapping word chunks from each page."""
    chunks = []
    with open(file_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            words = text.split()
            if not words:
                continue
            step = MAX_CHUNK_WORDS - CHUNK_OVERLAP
            for i in range(0, len(words), step):
                chunk_words = words[i: i + MAX_CHUNK_WORDS]
                chunk_text  = " ".join(chunk_words).strip()
                if chunk_text:
                    chunks.append({
                        "text": chunk_text,
                        "page": page_num + 1
                    })
    return chunks


def ingest_pdf(bucket_name: str, file_bytes: bytes, filename: str, description: str = "") -> tuple[bool, str, int]:
    """
    Index a PDF into the given bucket.
    Returns (success, message, chunk_count)
    """
    collection = get_collection(bucket_name)
    if collection is None:
        return False, f"Bucket '{bucket_name}' not found.", 0

    doc_id = str(uuid.uuid4())

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        chunks = extract_chunks_from_pdf(tmp_path)
        if not chunks:
            return False, "Could not extract text from PDF. It may be scanned/image-based.", 0

        ids, documents, metadatas = [], [], []
        for i, chunk in enumerate(chunks):
            ids.append(f"{doc_id}_chunk_{i}")
            documents.append(chunk["text"])
            metadatas.append({
                "doc_id":      doc_id,
                "filename":    filename,
                "description": description,
                "page":        chunk["page"],
                "bucket":      bucket_name
            })

        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        add_document_meta(bucket_name, doc_id, filename, description, len(chunks))
        return True, f"Indexed {len(chunks)} chunks from '{filename}'.", len(chunks)

    except Exception as e:
        return False, str(e), 0
    finally:
        os.unlink(tmp_path)


def delete_pdf(bucket_name: str, doc_id: str) -> tuple[bool, str]:
    """Remove all chunks of a document from ChromaDB."""
    collection = get_collection(bucket_name)
    if collection is None:
        return False, "Bucket not found."
    try:
        results = collection.get(where={"doc_id": doc_id})
        if results["ids"]:
            collection.delete(ids=results["ids"])
        delete_document_meta(bucket_name, doc_id)
        return True, "Document deleted."
    except Exception as e:
        return False, str(e)


# ── Retrieval ─────────────────────────────────────────

def retrieve_chunks(bucket_name: str, query: str, n: int = TOP_K_RESULTS) -> List[dict]:
    """Return top-n relevant chunks from the bucket."""
    collection = get_collection(bucket_name)
    if collection is None or collection.count() == 0:
        return []

    n = min(n, collection.count())
    results = collection.query(query_texts=[query], n_results=n)

    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({
            "text":     doc,
            "filename": meta.get("filename", ""),
            "page":     meta.get("page", "?"),
            "desc":     meta.get("description", "")
        })
    return chunks


# ── Generation ────────────────────────────────────────

def build_context(chunks: List[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks):
        parts.append(
            f"[Source {i+1}: {c['filename']} | Page {c['page']}]\n{c['text']}"
        )
    return "\n\n".join(parts)


def chat_with_bucket(
    bucket_name: str,
    user_message: str,
    conversation_history: List[dict]
) -> tuple[str, List[dict]]:
    """
    Full RAG pipeline:
    1. Retrieve relevant chunks
    2. Build context
    3. Call Groq LLM with history
    Returns (answer, sources)
    """
    chunks = retrieve_chunks(bucket_name, user_message)
    if not chunks:
        return (
            "⚠️ No relevant information found in this bucket. "
            "Please make sure PDFs have been uploaded.",
            []
        )

    context = build_context(chunks)

    system_prompt = f"""You are a helpful AI assistant that answers questions strictly based on the provided document context.

BUCKET: {bucket_name}

CONTEXT FROM DOCUMENTS:
{context}

STRICT RULES:
- Answer ONLY using information from the context above
- If the answer is not in the context, say: "I couldn't find relevant information in the {bucket_name} documents."
- Always mention the source file and page when referencing specific information
- Be concise, accurate, and well-structured
- Do not make up or infer information beyond what's in the context"""

    messages = []
    # Include last 6 turns of history for multi-turn context
    for msg in conversation_history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    client = get_groq_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": system_prompt}] + messages,
        max_tokens=1024,
        temperature=0.2
    )

    answer = response.choices[0].message.content

    # Deduplicate sources
    seen = set()
    sources = []
    for c in chunks:
        key = (c["filename"], c["page"])
        if key not in seen:
            seen.add(key)
            sources.append(c)

    return answer, sources
