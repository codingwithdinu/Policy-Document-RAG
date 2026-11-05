import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

# Set DATA_DIR=/var/data on Render when a persistent disk is mounted there.
DATA_DIR = Path(os.getenv("DATA_DIR", str(ROOT_DIR / "data"))).expanduser()
UPLOAD_DIR = DATA_DIR / "uploads"
VECTOR_INDEX_PATH = str(DATA_DIR / "vector_store" / "faiss_index" / "index")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
Path(VECTOR_INDEX_PATH).parent.mkdir(parents=True, exist_ok=True)
