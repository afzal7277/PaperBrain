import os
from dotenv import load_dotenv

load_dotenv()

# ── Groq ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.1-8b-instant"

# ── RAG ───────────────────────────────────────────────
EMBEDDING_MODEL  = "all-MiniLM-L6-v2"
TOP_K_RESULTS    = 5
MAX_CHUNK_WORDS  = 100
CHUNK_OVERLAP    = 20   # words overlap between chunks

# ── Paths ─────────────────────────────────────────────
DATA_DIR       = "data"
USERS_FILE     = os.path.join(DATA_DIR, "users.json")
CHROMA_DIR     = os.path.join(DATA_DIR, "chroma_db")

# ── App ───────────────────────────────────────────────
APP_TITLE      = "📄 RAG Chatbot"
APP_ICON       = "📄"
ADMIN_ROLE     = "admin"
USER_ROLE      = "user"
