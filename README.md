# 🧠 PaperBrain — AI-Powered PDF Chatbot

> Turn any PDF into a conversation. PaperBrain lets you chat with your documents using AI-powered bucket-based knowledge management.

Built with **Streamlit + Groq (Llama 3.1 8B) + ChromaDB + sentence-transformers** — 100% free, no paid services.

---

## ✨ Features

| Feature | Detail |
|---------|--------|
| 🪣 Dynamic Buckets | Create named buckets for any domain (Medical, Sales, Legal...) |
| 🔐 Role-Based Access | Admin and User roles with per-user bucket permissions |
| 🤖 Free LLM | Groq (Llama 3.1 8B) — no cost |
| 🔢 Local Embeddings | sentence-transformers — cached, runs locally, free |
| 🗄️ Vector Store | ChromaDB persistent store |
| 🔒 Password Hashing | bcrypt |
| 💬 Multi-turn Chat | Conversation history per bucket per session |
| 📝 Source Citations | Every answer shows PDF name + page number |
| 🏷️ PDF Tags | Add description/tag when uploading |
| 🚫 User Enable/Disable | Soft disable without deleting |
| 📊 Admin Dashboard | Stats per bucket and user |
| 👑 Admin Chat | Admin can test any bucket |

---

## 📁 Project Structure

```
PaperBrain/
├── app.py                  # Entry point — login + routing
├── auth.py                 # Auth, hashing, session, user management
├── admin.py                # Admin UI: dashboard, buckets, users, chat
├── chat.py                 # User chat UI
├── rag.py                  # RAG pipeline: ingest, retrieve, generate
├── bucket_manager.py       # Bucket CRUD + ChromaDB collections
├── config.py               # Settings and constants
├── run_tests.py            # Test runner — saves results to test_results/
├── pytest.ini              # Pytest configuration
├── data/
│   ├── users.json          # User store (auto-created on first run)
│   ├── buckets.json        # Bucket metadata (auto-created)
│   └── chroma_db/          # Vector store (auto-created)
├── tests/
│   ├── conftest.py         # Shared fixtures with guaranteed cleanup
│   ├── test_auth.py        # Auth unit tests (20 tests)
│   ├── test_buckets.py     # Bucket unit tests (20 tests)
│   ├── test_rag.py         # RAG pipeline tests (18 tests)
│   └── test_qa_eval.py     # QA scoring + bucket isolation tests
├── test_results/           # Auto-created, stores all test output
├── requirements.txt
└── .env
```

---

## 🚀 Setup & Run

### Step 1 — Create virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Get a free Groq API key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free, no credit card)
3. Create an API key

### Step 4 — Set environment variables

```bash
cp env.example .env
# Edit .env:
GROQ_API_KEY=your_groq_key_here
HF_TOKEN=your_hf_token_here     # optional — silences HF warnings
```

Get a free HuggingFace token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) → Read access only.

### Step 5 — Run the app

```bash
streamlit run app.py
# Open → http://localhost:8501
```

---

## 👥 Default Credentials

| Username | Password | Role |
|----------|----------|------|
| `admin`  | `admin123` | Admin |
| `user`   | `user123`  | User |

⚠️ Change these after first login!

---

## 🔄 Workflow

### Admin
1. Login → **Buckets** → Create bucket → Upload PDFs
2. **Users** → Create users → Assign bucket permissions
3. **Chat** → Test bucket quality

### User
1. Login → Select assigned bucket → Chat
2. Every answer shows source PDF + page number

---

## 🧪 Running Tests

### Install test dependencies

```bash
pip install pytest pytest-xdist reportlab
pip install pytest-json-report   # optional, for JSON output
```

### Commands

```bash
# All tests (saves results to test_results/)
python run_tests.py

# Unit tests only — fast, no API calls
python run_tests.py --unit

# QA evaluation — needs Groq + PDFs uploaded
python run_tests.py --qa

# Parallel execution (fastest)
python run_tests.py --parallel

# Direct pytest commands
pytest                                          # all tests
pytest tests/test_auth.py -v                   # single file
pytest tests/test_auth.py::TestPasswordHashing # single class
pytest -n auto                                 # parallel
```

### Test results saved to `test_results/`

```
test_results/
├── latest.json                      # most recent run summary
├── result_20240101_120000.txt        # human-readable report
└── result_20240101_120000.json       # JSON report (if pytest-json-report installed)
```

### QA tests — prerequisites

Upload sample PDFs via admin panel before running QA tests:

| PDF | Bucket name |
|-----|-------------|
| `medical_reference.pdf` | `Medical` |
| `sales_playbook_q3.pdf` | `Sales` |
| `hr_employee_handbook.pdf` | `HR` |

QA tests are **skipped** (not failed) if bucket is missing or empty.

---

## 🧠 RAG Pipeline

```
PDF Upload:
  pypdf → extract text → 100-word chunks (20-word overlap)
  → sentence-transformers embed (cached) → ChromaDB (per bucket)

User Query:
  embed → cosine similarity → top-5 chunks
  → Groq Llama 3.1 8B → answer + sources (PDF name + page)
```

---

## ⚙️ Configuration (`config.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `GROQ_MODEL` | `llama-3.1-8b-instant` | LLM model |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `TOP_K_RESULTS` | `5` | Chunks per query |
| `MAX_CHUNK_WORDS` | `100` | Words per chunk |
| `CHUNK_OVERLAP` | `20` | Overlap between chunks |

---

## 💰 Cost — 100% Free

Groq · ChromaDB · sentence-transformers · Streamlit — all free and open source.

---

## 📝 License

MIT