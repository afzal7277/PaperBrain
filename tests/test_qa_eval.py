"""
test_qa_eval.py — QA Evaluation tests.
Runs predefined Q&A pairs against live buckets and scores answers.
Skipped automatically if bucket/docs not found.
"""
import pytest
import time


# ── QA Test Cases ─────────────────────────────────────
QA_CASES = {
    "Medical": [
        {
            "question": "What is the first-line treatment for hypertension?",
            "keywords": ["ACE inhibitors", "lisinopril", "ARB", "calcium channel", "thiazide"],
            "min_score": 0.4
        },
        {
            "question": "What blood glucose level confirms Type 2 diabetes?",
            "keywords": ["126", "mg/dL", "HbA1c", "6.5"],
            "min_score": 0.4
        },
        {
            "question": "What is the target HbA1c for most diabetes patients?",
            "keywords": ["7%", "below 7", "HbA1c"],
            "min_score": 0.4
        },
        {
            "question": "What drug interaction has high severity between Warfarin and Aspirin?",
            "keywords": ["bleeding", "warfarin", "aspirin"],
            "min_score": 0.4
        },
        {
            "question": "What is the emergency treatment for anaphylaxis?",
            "keywords": ["epinephrine", "0.3mg", "thigh"],
            "min_score": 0.4
        },
    ],
    "Sales": [
        {
            "question": "What was the total Q3 2024 revenue?",
            "keywords": ["4.2 million", "$4.2"],
            "min_score": 0.4
        },
        {
            "question": "What is the pricing for the Enterprise plan?",
            "keywords": ["2,000", "custom", "minimum"],
            "min_score": 0.4
        },
        {
            "question": "What is the Q4 revenue target?",
            "keywords": ["5.1 million", "$5.1"],
            "min_score": 0.4
        },
        {
            "question": "What discount do annual contracts receive?",
            "keywords": ["20%", "annual", "discount"],
            "min_score": 0.4
        },
        {
            "question": "What framework is used for sales qualification?",
            "keywords": ["MEDDIC", "qualification", "metrics"],
            "min_score": 0.4
        },
    ],
    "HR_Policies": [
        {
            "question": "How many days of annual leave do employees get?",
            "keywords": ["20 days", "20"],
            "min_score": 0.4
        },
        {
            "question": "What is the maternity leave duration?",
            "keywords": ["26 weeks", "maternity"],
            "min_score": 0.4
        },
        {
            "question": "How often are performance reviews conducted?",
            "keywords": ["bi-annually", "June", "December"],
            "min_score": 0.4
        },
        {
            "question": "How many days per week can employees work remotely?",
            "keywords": ["3 days", "remote"],
            "min_score": 0.4
        },
        {
            "question": "What happens to an employee rated 2 or below in performance?",
            "keywords": ["90-day", "Performance Improvement Plan"],
            "min_score": 0.4
        },
    ]
}


# ── Helpers ───────────────────────────────────────────
def score_answer(answer: str, keywords: list) -> float:
    """Score 0.0–1.0 based on keyword hits."""
    answer_lower = answer.lower()
    hits = sum(1 for kw in keywords if kw.lower() in answer_lower)
    return hits / len(keywords) if keywords else 0.0


def bucket_has_docs(bucket_name: str) -> bool:
    from bucket_manager import list_buckets, list_documents
    return bucket_name in list_buckets() and len(list_documents(bucket_name)) > 0


# ── Fixtures ──────────────────────────────────────────
@pytest.fixture(scope="module")
def groq_available():
    """Skip all QA tests if Groq key is missing."""
    from config import GROQ_API_KEY
    if not GROQ_API_KEY or len(GROQ_API_KEY) < 10:
        pytest.skip("GROQ_API_KEY not set — skipping QA evaluation")


# ── Test Classes ──────────────────────────────────────
class TestMedicalBucket:
    @pytest.fixture(autouse=True)
    def skip_if_no_bucket(self):
        if not bucket_has_docs("Medical"):
            pytest.skip("Medical bucket not found or empty — upload medical_reference.pdf first")

    @pytest.mark.parametrize("case", QA_CASES["Medical"])
    def test_medical_qa(self, case, groq_available):
        from rag import chat_with_bucket

        start = time.time()
        answer, sources = chat_with_bucket("Medical", case["question"], [])
        elapsed = round(time.time() - start, 2)

        score = score_answer(answer, case["keywords"])

        # Always assert sources exist
        assert len(sources) > 0, "No sources returned — retrieval may have failed"

        # Assert response time is reasonable
        assert elapsed < 30, f"Response took too long: {elapsed}s"

        # Assert score meets minimum
        assert score >= case["min_score"], (
            f"\nQuestion: {case['question']}"
            f"\nScore: {score:.0%} (min: {case['min_score']:.0%})"
            f"\nExpected keywords: {case['keywords']}"
            f"\nAnswer received: {answer[:300]}"
        )


class TestSalesBucket:
    @pytest.fixture(autouse=True)
    def skip_if_no_bucket(self):
        if not bucket_has_docs("Sales"):
            pytest.skip("Sales bucket not found or empty — upload sales_playbook_q3.pdf first")

    @pytest.mark.parametrize("case", QA_CASES["Sales"])
    def test_sales_qa(self, case, groq_available):
        from rag import chat_with_bucket

        start = time.time()
        answer, sources = chat_with_bucket("Sales", case["question"], [])
        elapsed = round(time.time() - start, 2)

        score = score_answer(answer, case["keywords"])

        assert len(sources) > 0, "No sources returned"
        assert elapsed < 30, f"Response too slow: {elapsed}s"
        assert score >= case["min_score"], (
            f"\nQuestion: {case['question']}"
            f"\nScore: {score:.0%} (min: {case['min_score']:.0%})"
            f"\nExpected keywords: {case['keywords']}"
            f"\nAnswer: {answer[:300]}"
        )


class TestHRBucket:
    @pytest.fixture(autouse=True)
    def skip_if_no_bucket(self):
        if not bucket_has_docs("HR_Policies"):
            pytest.skip("HR_Policies bucket not found or empty — upload hr_employee_handbook.pdf first")

    @pytest.mark.parametrize("case", QA_CASES["HR_Policies"])
    def test_hr_qa(self, case, groq_available):
        from rag import chat_with_bucket

        start = time.time()
        answer, sources = chat_with_bucket("HR_Policies", case["question"], [])
        elapsed = round(time.time() - start, 2)

        score = score_answer(answer, case["keywords"])

        assert len(sources) > 0, "No sources returned"
        assert elapsed < 30, f"Response too slow: {elapsed}s"
        assert score >= case["min_score"], (
            f"\nQuestion: {case['question']}"
            f"\nScore: {score:.0%} (min: {case['min_score']:.0%})"
            f"\nExpected keywords: {case['keywords']}"
            f"\nAnswer: {answer[:300]}"
        )


class TestBucketIsolation:
    """Verify bucket isolation — answers must come from the right bucket only."""

    @pytest.fixture(autouse=True)
    def skip_if_no_buckets(self):
        if not bucket_has_docs("Medical") or not bucket_has_docs("Sales"):
            pytest.skip("Need both Medical and Sales buckets for isolation test")

    def test_medical_query_not_answered_by_sales(self, groq_available):
        """A medical question asked to Sales bucket should NOT find relevant info."""
        from rag import chat_with_bucket
        answer, _ = chat_with_bucket(
            "Sales",
            "What is the dosage of Epinephrine for anaphylaxis?",
            []
        )
        answer_lower = answer.lower()
        # Should say it can't find info, not give a medical answer
        no_info_phrases = ["couldn't find", "not find", "no information", "not available", "no relevant"]
        assert any(phrase in answer_lower for phrase in no_info_phrases), (
            f"Sales bucket answered a medical question — bucket isolation broken!\nAnswer: {answer[:300]}"
        )

    def test_sales_query_not_answered_by_medical(self, groq_available):
        """A sales question asked to Medical bucket should NOT find relevant info."""
        from rag import chat_with_bucket
        answer, _ = chat_with_bucket(
            "Medical",
            "What was the Q3 revenue and Q4 sales target?",
            []
        )
        answer_lower = answer.lower()
        no_info_phrases = ["couldn't find", "not find", "no information", "not available", "no relevant"]
        assert any(phrase in answer_lower for phrase in no_info_phrases), (
            f"Medical bucket answered a sales question — bucket isolation broken!\nAnswer: {answer[:300]}"
        )
