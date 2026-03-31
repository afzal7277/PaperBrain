# 📄 RAG Chatbot — Multi-Bucket, Role-Based PDF Assistant

A fully free, production-ready RAG chatbot built with Streamlit + Groq + ChromaDB.
Upload PDFs into domain-specific buckets, assign users to buckets, and chat with your documents.

---

## ✨ Features

| Feature | Detail |
|---------|--------|
| 🪣 Dynamic Buckets | Create named buckets for any domain (Medical, Sales, Legal...) |
| 🔐 Role-Based Access | Admin and User roles with per-user bucket permissions |
| 🤖 Free LLM | Groq (Llama 3.1 8B) — no cost |
| 🔢 Local Embeddings | sentence-transformers — runs locally, free |
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
rag-chatbot/
├── app.py               # Entry point — login + routing
├── auth.py              # Auth, hashing, session, user management
├── admin.py             # Admin UI: dashboard, buckets, users, chat
├── chat.py              # User chat UI
├── rag.py               # RAG pipeline: ingest, retrieve, generate
├── bucket_manager.py    # Bucket CRUD + ChromaDB collections
├── config.py            # Settings and constants
├── data/
│   ├── users.json       # User store (auto-created)
│   ├── buckets.json     # Bucket metadata (auto-created)
│   └── chroma_db/       # Vector store (auto-created)
├── requirements.txt
└── .env
```

---

## 🚀 Setup & Run

### 1. Clone / Download the project

```bash
cd rag-chatbot
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get a free Groq API key

- Go to https://console.groq.com
- Sign up (free, no credit card)
- Create an API key

### 5. Set environment variable

```bash
# Create .env file
echo "GROQ_API_KEY=your_key_here" > .env
```

### 6. Run the app

```bash
streamlit run app.py
```

Open → http://localhost:8501

---

## 👥 Default Credentials

| Username | Password | Role |
|----------|----------|------|
| admin    | admin123 | Admin |
| user     | user123  | User |

⚠️ Change these immediately after first login!

---

## 🔄 Workflow

### Admin Flow
1. Login as admin
2. Go to **Buckets** tab → Create a bucket (e.g. "Medical")
3. Upload PDFs into the bucket with optional tags
4. Go to **Users** tab → Create users, assign bucket permissions
5. Go to **Chat** tab → Test the bucket quality

### User Flow
1. Login as user
2. See only assigned buckets in sidebar
3. Select a bucket → Chat with its documents
4. Every answer shows source PDF + page number

---

## 🧠 RAG Pipeline

```
PDF Upload:
  pypdf → extract text → split into 100-word chunks (20-word overlap)
  → sentence-transformers embed → ChromaDB collection (per bucket)

User Query:
  embed query → cosine similarity search → top-5 chunks
  → build context → Groq Llama 3.1 8B → answer + sources
```

---

## ⚙️ Configuration (`config.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| GROQ_MODEL | llama-3.1-8b-instant | LLM model |
| EMBEDDING_MODEL | all-MiniLM-L6-v2 | Embedding model |
| TOP_K_RESULTS | 5 | Chunks retrieved per query |
| MAX_CHUNK_WORDS | 100 | Words per chunk |
| CHUNK_OVERLAP | 20 | Overlap between chunks |

---

## 💰 Cost

**100% Free:**
- Groq: Free tier (rate limited but generous)
- ChromaDB: Open source
- sentence-transformers: Open source, runs locally
- Streamlit: Open source

---

## 📝 License

MIT — free to use and modify.
