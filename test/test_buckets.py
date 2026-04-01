"""
test_buckets.py — Bucket module tests.
Tests: CRUD, ChromaDB collections, metadata, stats, cleanup.
"""
import pytest


class TestBucketCreation:
    def test_create_bucket_success(self, temp_bucket):
        from bucket_manager import list_buckets
        assert temp_bucket in list_buckets()

    def test_bucket_has_description(self, temp_bucket):
        from bucket_manager import get_bucket_info
        info = get_bucket_info(temp_bucket)
        assert "description" in info
        assert info["description"] == "Pytest test bucket"

    def test_bucket_has_collection_name(self, temp_bucket):
        from bucket_manager import get_bucket_info
        info = get_bucket_info(temp_bucket)
        assert "collection" in info
        assert len(info["collection"]) > 0

    def test_bucket_starts_with_no_documents(self, temp_bucket):
        from bucket_manager import list_documents
        docs = list_documents(temp_bucket)
        assert docs == {}

    def test_duplicate_bucket_rejected(self, temp_bucket):
        from bucket_manager import create_bucket
        ok, msg = create_bucket(temp_bucket, "duplicate")
        assert not ok
        assert "already exists" in msg.lower()

    def test_empty_name_rejected(self):
        from bucket_manager import create_bucket
        ok, msg = create_bucket("", "desc")
        assert not ok

    def test_whitespace_name_rejected(self):
        from bucket_manager import create_bucket
        ok, msg = create_bucket("   ", "desc")
        assert not ok


class TestBucketDeletion:
    def test_delete_removes_from_list(self):
        from bucket_manager import create_bucket, delete_bucket, list_buckets
        create_bucket("pytest_del_tmp", "")
        assert "pytest_del_tmp" in list_buckets()
        delete_bucket("pytest_del_tmp")
        assert "pytest_del_tmp" not in list_buckets()

    def test_delete_nonexistent_bucket(self):
        from bucket_manager import delete_bucket
        ok, msg = delete_bucket("pytest_nonexistent_bucket")
        assert not ok

    def test_delete_removes_from_user_permissions(self, temp_bucket):
        """Deleting a bucket should remove it from all user bucket lists."""
        from auth import create_user, delete_user, _load_users
        from bucket_manager import delete_bucket

        # Give user access to the bucket
        create_user("pytest_permuser_tmp", "pass123", "user", [temp_bucket])

        # Delete the bucket
        delete_bucket(temp_bucket)

        # User's bucket list should no longer contain it
        users = _load_users()
        if "pytest_permuser_tmp" in users:
            assert temp_bucket not in users["pytest_permuser_tmp"]["buckets"]

        # Cleanup user
        delete_user("pytest_permuser_tmp")


class TestBucketCollection:
    def test_collection_created_in_chromadb(self, temp_bucket):
        from bucket_manager import get_collection
        col = get_collection(temp_bucket)
        assert col is not None

    def test_collection_starts_empty(self, temp_bucket):
        from bucket_manager import get_collection
        col = get_collection(temp_bucket)
        assert col.count() == 0

    def test_nonexistent_bucket_returns_none(self):
        from bucket_manager import get_collection
        col = get_collection("pytest_nonexistent_tmp")
        assert col is None


class TestDocumentMetadata:
    def test_add_document_meta(self, temp_bucket):
        from bucket_manager import add_document_meta, list_documents
        add_document_meta(temp_bucket, "doc123", "test.pdf", "Test desc", 42)
        docs = list_documents(temp_bucket)
        assert "doc123" in docs
        assert docs["doc123"]["filename"] == "test.pdf"
        assert docs["doc123"]["chunks"] == 42

    def test_delete_document_meta(self, temp_bucket):
        from bucket_manager import add_document_meta, delete_document_meta, list_documents
        add_document_meta(temp_bucket, "doc456", "remove.pdf", "", 10)
        delete_document_meta(temp_bucket, "doc456")
        docs = list_documents(temp_bucket)
        assert "doc456" not in docs

    def test_list_documents_empty_bucket(self, temp_bucket):
        from bucket_manager import list_documents
        docs = list_documents(temp_bucket)
        assert isinstance(docs, dict)
        assert len(docs) == 0


class TestBucketStats:
    def test_stats_returns_correct_structure(self):
        from bucket_manager import get_stats
        stats = get_stats()
        assert "total_buckets" in stats
        assert "total_docs" in stats
        assert "total_chunks" in stats
        assert "buckets" in stats
        assert isinstance(stats["buckets"], list)

    def test_stats_count_increases_after_bucket_creation(self):
        from bucket_manager import create_bucket, delete_bucket, get_stats
        before = get_stats()["total_buckets"]
        create_bucket("pytest_stats_tmp", "")
        after = get_stats()["total_buckets"]
        delete_bucket("pytest_stats_tmp")
        assert after == before + 1

    def test_stats_count_decreases_after_deletion(self):
        from bucket_manager import create_bucket, delete_bucket, get_stats
        create_bucket("pytest_statsdel_tmp", "")
        before = get_stats()["total_buckets"]
        delete_bucket("pytest_statsdel_tmp")
        after = get_stats()["total_buckets"]
        assert after == before - 1


class TestSafeCollectionName:
    def test_spaces_replaced(self):
        from bucket_manager import _safe_collection_name
        name = _safe_collection_name("My Bucket Name")
        assert " " not in name

    def test_special_chars_replaced(self):
        from bucket_manager import _safe_collection_name
        name = _safe_collection_name("bucket@#$%name!")
        assert all(c.isalnum() or c == "_" for c in name)

    def test_name_starts_with_letter(self):
        from bucket_manager import _safe_collection_name
        name = _safe_collection_name("123bucket")
        assert name[0].isalpha()

    def test_long_name_truncated(self):
        from bucket_manager import _safe_collection_name
        name = _safe_collection_name("a" * 100)
        assert len(name) <= 63