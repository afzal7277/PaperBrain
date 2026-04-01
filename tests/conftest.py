"""
conftest.py — Shared fixtures for PaperBrain test suite.
All fixtures use yield for guaranteed cleanup on pass AND fail.
"""
import os
import sys
import warnings
import tempfile
import pytest

# ── Suppress noise ────────────────────────────────────
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore")

# ── Add project root to path ──────────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()


# ══════════════════════════════════════════════════════
# AUTH FIXTURES
# ══════════════════════════════════════════════════════

@pytest.fixture
def temp_user():
    """Create a test user, yield username, delete after test."""
    from auth import create_user, delete_user
    username = "pytest_user_tmp"
    create_user(username, "testpass123", "user", [])
    yield username
    # ── always runs ──
    delete_user(username)


@pytest.fixture
def temp_admin_user():
    """Create a test admin user, yield username, delete after test."""
    from auth import create_user, delete_user
    username = "pytest_admin_tmp"
    create_user(username, "adminpass123", "admin", ["*"])
    yield username
    # ── always runs ──
    delete_user(username)


# ══════════════════════════════════════════════════════
# BUCKET FIXTURES
# ══════════════════════════════════════════════════════

@pytest.fixture
def temp_bucket():
    """Create a test bucket, yield name, delete after test."""
    from bucket_manager import create_bucket, delete_bucket
    name = "pytest_bucket_tmp"
    create_bucket(name, "Pytest test bucket")
    yield name
    # ── always runs ──
    delete_bucket(name)


@pytest.fixture
def temp_bucket_with_pdf(tmp_path):
    """
    Create a bucket + index a real PDF into it.
    Yields (bucket_name, doc_id).
    Deletes both on teardown.
    """
    from bucket_manager import create_bucket, delete_bucket
    from rag import ingest_pdf
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    # Create bucket
    bucket_name = "pytest_bucket_pdf_tmp"
    create_bucket(bucket_name, "Pytest bucket with PDF")

    # Create a real PDF using tmp_path (auto-cleaned by pytest)
    pdf_path = tmp_path / "test_doc.pdf"
    doc = SimpleDocTemplate(str(pdf_path))
    styles = getSampleStyleSheet()
    doc.build([
        Paragraph("PaperBrain Test Document", styles["Title"]),
        Spacer(1, 12),
        Paragraph(
            "The sky is blue and the grass is green. "
            "PaperBrain is an AI-powered document assistant. "
            "RAG stands for Retrieval Augmented Generation. "
            "ChromaDB is used as the vector store. "
            "Groq provides fast LLM inference. " * 10,
            styles["Normal"]
        ),
        Paragraph(
            "The capital of France is Paris. "
            "Python is a popular programming language. "
            "Machine learning models require training data. "
            "Embeddings convert text into numerical vectors. " * 10,
            styles["Normal"]
        ),
    ])

    # Ingest PDF
    with open(str(pdf_path), "rb") as f:
        pdf_bytes = f.read()

    ok, msg, chunks = ingest_pdf(bucket_name, pdf_bytes, "test_doc.pdf", "Pytest test document")
    assert ok, f"PDF ingestion failed in fixture: {msg}"

    yield bucket_name

    # ── always runs ──
    delete_bucket(bucket_name)


# ══════════════════════════════════════════════════════
# PDF FIXTURES
# ══════════════════════════════════════════════════════

@pytest.fixture
def temp_pdf(tmp_path):
    """
    Generate a temp PDF using pytest's tmp_path.
    tmp_path is automatically cleaned by pytest after test.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    pdf_path = tmp_path / "sample.pdf"
    doc = SimpleDocTemplate(str(pdf_path))
    styles = getSampleStyleSheet()
    doc.build([
        Paragraph("Test Document Title", styles["Title"]),
        Paragraph("This is test content for unit testing. " * 30, styles["Normal"]),
        Paragraph("Second paragraph with more content. " * 30, styles["Normal"]),
    ])
    yield str(pdf_path)
    # tmp_path cleanup is handled automatically by pytest


@pytest.fixture
def large_temp_pdf(tmp_path):
    """Generate a larger PDF with multiple pages for chunk testing."""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet

    pdf_path = tmp_path / "large_sample.pdf"
    doc = SimpleDocTemplate(str(pdf_path))
    styles = getSampleStyleSheet()
    story = []
    for i in range(5):
        story.append(Paragraph(f"Page {i+1} Title", styles["Heading1"]))
        story.append(Paragraph(f"Content for page {i+1}. " * 100, styles["Normal"]))
        if i < 4:
            story.append(PageBreak())
    doc.build(story)
    yield str(pdf_path)