import json
import os
import chromadb
import streamlit as st
from chromadb.utils import embedding_functions
from config import CHROMA_DIR, EMBEDDING_MODEL, DATA_DIR

# ── ChromaDB client (persistent) ──────────────────────
_client = None

def get_chroma_client():
    global _client
    if _client is None:
        os.makedirs(CHROMA_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _client


@st.cache_resource(show_spinner="Loading embedding model...")
def get_embedding_fn():
    """Cached embedding function — loads once, reused across all sessions."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )


def _bucket_meta_file():
    return os.path.join(DATA_DIR, "buckets.json")


def _load_bucket_meta() -> dict:
    path = _bucket_meta_file()
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save_bucket_meta(meta: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(_bucket_meta_file(), "w") as f:
        json.dump(meta, f, indent=2)


def _safe_collection_name(bucket_name: str) -> str:
    """ChromaDB collection names must be alphanumeric + underscores."""
    import re
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", bucket_name)
    if not safe[0].isalpha():
        safe = "b_" + safe
    return safe[:63]  # max 63 chars


# ── Bucket CRUD ───────────────────────────────────────

def list_buckets() -> list:
    meta = _load_bucket_meta()
    return list(meta.keys())


def get_bucket_info(bucket_name: str) -> dict:
    meta = _load_bucket_meta()
    return meta.get(bucket_name, {})


def create_bucket(bucket_name: str, description: str = "") -> tuple[bool, str]:
    if not bucket_name.strip():
        return False, "Bucket name cannot be empty."
    meta = _load_bucket_meta()
    if bucket_name in meta:
        return False, f"Bucket '{bucket_name}' already exists."

    # Create ChromaDB collection
    client = get_chroma_client()
    col_name = _safe_collection_name(bucket_name)
    client.get_or_create_collection(
        name=col_name,
        embedding_function=get_embedding_fn()
    )

    meta[bucket_name] = {
        "description": description,
        "collection": col_name,
        "documents": {}
    }
    _save_bucket_meta(meta)
    return True, ""


def delete_bucket(bucket_name: str) -> tuple[bool, str]:
    meta = _load_bucket_meta()
    if bucket_name not in meta:
        return False, f"Bucket '{bucket_name}' not found."

    # Delete ChromaDB collection
    client = get_chroma_client()
    col_name = meta[bucket_name]["collection"]
    try:
        client.delete_collection(col_name)
    except Exception:
        pass

    del meta[bucket_name]
    _save_bucket_meta(meta)

    # Remove bucket from all users
    from auth import get_all_users, update_user_buckets
    users = get_all_users()
    for uname, udata in users.items():
        if bucket_name in udata.get("buckets", []):
            new_buckets = [b for b in udata["buckets"] if b != bucket_name]
            update_user_buckets(uname, new_buckets)

    return True, ""


def get_collection(bucket_name: str):
    meta = _load_bucket_meta()
    if bucket_name not in meta:
        return None
    col_name = meta[bucket_name]["collection"]
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=col_name,
        embedding_function=get_embedding_fn()
    )


# ── Document management ───────────────────────────────

def add_document_meta(bucket_name: str, doc_id: str, filename: str, description: str, chunks: int):
    meta = _load_bucket_meta()
    if bucket_name not in meta:
        return
    meta[bucket_name]["documents"][doc_id] = {
        "filename": filename,
        "description": description,
        "chunks": chunks
    }
    _save_bucket_meta(meta)


def delete_document_meta(bucket_name: str, doc_id: str):
    meta = _load_bucket_meta()
    if bucket_name in meta and doc_id in meta[bucket_name]["documents"]:
        del meta[bucket_name]["documents"][doc_id]
        _save_bucket_meta(meta)


def list_documents(bucket_name: str) -> dict:
    meta = _load_bucket_meta()
    return meta.get(bucket_name, {}).get("documents", {})


# ── Stats ─────────────────────────────────────────────

def get_stats() -> dict:
    meta = _load_bucket_meta()
    client = get_chroma_client()
    stats = {"buckets": [], "total_buckets": 0, "total_docs": 0, "total_chunks": 0}

    for bname, bdata in meta.items():
        col_name = bdata.get("collection")
        chunk_count = 0
        try:
            col = client.get_collection(col_name, embedding_function=get_embedding_fn())
            chunk_count = col.count()
        except Exception:
            pass

        doc_count = len(bdata.get("documents", {}))
        stats["buckets"].append({
            "name": bname,
            "description": bdata.get("description", ""),
            "docs": doc_count,
            "chunks": chunk_count
        })
        stats["total_docs"]   += doc_count
        stats["total_chunks"] += chunk_count

    stats["total_buckets"] = len(meta)
    return stats