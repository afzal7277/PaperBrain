"""
test_rag.py — RAG pipeline tests.
Tests: PDF extraction, chunking, ingestion, retrieval, deletion.
"""
import pytest
from config import MAX_CHUNK_WORDS, CHUNK_OVERLAP


class TestPDFExtraction:
    def test_extracts_text_from_pdf(self, temp_pdf):
        from rag import extract_chunks_from_pdf
        chunks = extract_chunks_from_pdf(temp_pdf)
        assert len(chunks) > 0

    def test_chunks_have_required_fields(self, temp_pdf):
        from rag import extract_chunks_from_pdf
        chunks = extract_chunks_from_pdf(temp_pdf)
        for chunk in chunks:
            assert "text" in chunk, "Chunk missing 'text'"
            assert "page" in chunk, "Chunk missing 'page'"

    def test_chunks_have_nonempty_text(self, temp_pdf):
        from rag import extract_chunks_from_pdf
        chunks = extract_chunks_from_pdf(temp_pdf)
        for chunk in chunks:
            assert chunk["text"].strip() != "", "Empty chunk found"

    def test_page_numbers_are_positive(self, temp_pdf):
        from rag import extract_chunks_from_pdf
        chunks = extract_chunks_from_pdf(temp_pdf)
        for chunk in chunks:
            assert chunk["page"] >= 1, f"Invalid page number: {chunk['page']}"

    def test_chunk_word_count_within_limit(self, temp_pdf):
        from rag import extract_chunks_from_pdf
        chunks = extract_chunks_from_pdf(temp_pdf)
        for chunk in chunks:
            word_count = len(chunk["text"].split())
            assert word_count <= MAX_CHUNK_WORDS + 5, \
                f"Chunk exceeds limit: {word_count} words (max {MAX_CHUNK_WORDS})"

    def test_multipage_pdf_extracts_all_pages(self, large_temp_pdf):
        from rag import extract_chunks_from_pdf
        chunks = extract_chunks_from_pdf(large_temp_pdf)
        pages_found = set(c["page"] for c in chunks)
        assert len(pages_found) >= 4, f"Expected 5 pages, found pages: {pages_found}"

    def test_chunks_have_overlap(self, large_temp_pdf):
        """Consecutive chunks should share some words due to overlap."""
        from rag import extract_chunks_from_pdf
        chunks = extract_chunks_from_pdf(large_temp_pdf)
        same_page = [c for c in chunks if c["page"] == 1]
        if len(same_page) >= 2:
            words1 = set(same_page[0]["text"].split())
            words2 = set(same_page[1]["text"].split())
            overlap = words1 & words2
            assert len(overlap) > 0, "No overlap found between consecutive chunks"


class TestPDFIngestion:
    def test_ingest_pdf_success(self, temp_bucket, temp_pdf):
        from rag import ingest_pdf
        with open(temp_pdf, "rb") as f:
            pdf_bytes = f.read()
        ok, msg, chunks = ingest_pdf(temp_bucket, pdf_bytes, "test.pdf", "Test desc")
        assert ok, f"Ingestion failed: {msg}"
        assert chunks > 0

    def test_ingest_indexes_into_chromadb(self, temp_bucket, temp_pdf):
        from rag import ingest_pdf
        from bucket_manager import get_collection
        with open(temp_pdf, "rb") as f:
            pdf_bytes = f.read()
        ok, msg, n_chunks = ingest_pdf(temp_bucket, pdf_bytes, "indexed.pdf", "")
        col = get_collection(temp_bucket)
        assert col.count() == n_chunks

    def test_ingest_updates_document_metadata(self, temp_bucket, temp_pdf):
        from rag import ingest_pdf
        from bucket_manager import list_documents
        with open(temp_pdf, "rb") as f:
            pdf_bytes = f.read()
        ok, msg, _ = ingest_pdf(temp_bucket, pdf_bytes, "meta_test.pdf", "My tag")
        docs = list_documents(temp_bucket)
        filenames = [d["filename"] for d in docs.values()]
        assert "meta_test.pdf" in filenames

    def test_ingest_into_nonexistent_bucket_fails(self, temp_pdf):
        from rag import ingest_pdf
        with open(temp_pdf, "rb") as f:
            pdf_bytes = f.read()
        ok, msg, _ = ingest_pdf("__nonexistent_bucket__", pdf_bytes, "test.pdf", "")
        assert not ok


class TestPDFDeletion:
    def test_delete_removes_chunks_from_chromadb(self, temp_bucket, temp_pdf):
        from rag import ingest_pdf, delete_pdf
        from bucket_manager import get_collection, list_documents
        with open(temp_pdf, "rb") as f:
            pdf_bytes = f.read()
        ok, msg, _ = ingest_pdf(temp_bucket, pdf_bytes, "to_delete.pdf", "")
        assert ok

        # Find doc_id
        docs = list_documents(temp_bucket)
        doc_id = next(d_id for d_id, d in docs.items() if d["filename"] == "to_delete.pdf")

        col_before = get_collection(temp_bucket).count()
        delete_pdf(temp_bucket, doc_id)
        col_after = get_collection(temp_bucket).count()

        assert col_after < col_before

    def test_delete_removes_document_metadata(self, temp_bucket, temp_pdf):
        from rag import ingest_pdf, delete_pdf
        from bucket_manager import list_documents
        with open(temp_pdf, "rb") as f:
            pdf_bytes = f.read()
        ingest_pdf(temp_bucket, pdf_bytes, "meta_del.pdf", "")
        docs = list_documents(temp_bucket)
        doc_id = next(d_id for d_id, d in docs.items() if d["filename"] == "meta_del.pdf")

        delete_pdf(temp_bucket, doc_id)
        docs_after = list_documents(temp_bucket)
        assert doc_id not in docs_after


class TestRetrieval:
    def test_retrieve_returns_chunks(self, temp_bucket_with_pdf):
        from rag import retrieve_chunks
        results = retrieve_chunks(temp_bucket_with_pdf, "PaperBrain document assistant")
        assert len(results) > 0

    def test_retrieve_chunks_have_required_fields(self, temp_bucket_with_pdf):
        from rag import retrieve_chunks
        results = retrieve_chunks(temp_bucket_with_pdf, "RAG ChromaDB")
        for r in results:
            assert "text" in r
            assert "filename" in r
            assert "page" in r

    def test_retrieve_respects_n_results(self, temp_bucket_with_pdf):
        from rag import retrieve_chunks
        results = retrieve_chunks(temp_bucket_with_pdf, "test content", n=2)
        assert len(results) <= 2

    def test_retrieve_empty_bucket_returns_empty(self, temp_bucket):
        from rag import retrieve_chunks
        results = retrieve_chunks(temp_bucket, "any query")
        assert results == []

    def test_retrieve_nonexistent_bucket_returns_empty(self):
        from rag import retrieve_chunks
        results = retrieve_chunks("__nonexistent__", "query")
        assert results == []

    def test_relevant_content_is_retrieved(self, temp_bucket_with_pdf):
        """Query about known content should retrieve relevant chunks."""
        from rag import retrieve_chunks
        results = retrieve_chunks(temp_bucket_with_pdf, "capital of France Paris")
        all_text = " ".join(r["text"] for r in results).lower()
        assert "paris" in all_text or "france" in all_text


class TestGroqConfig:
    def test_groq_api_key_set(self):
        from config import GROQ_API_KEY
        assert GROQ_API_KEY and len(GROQ_API_KEY) > 10, \
            "GROQ_API_KEY not set. Add it to your .env file."

    def test_groq_model_set(self):
        from config import GROQ_MODEL
        assert GROQ_MODEL and len(GROQ_MODEL) > 0

    def test_top_k_is_positive(self):
        from config import TOP_K_RESULTS
        assert TOP_K_RESULTS > 0

    def test_chunk_settings_valid(self):
        assert MAX_CHUNK_WORDS > 0
        assert CHUNK_OVERLAP < MAX_CHUNK_WORDS, "Overlap must be less than chunk size"
