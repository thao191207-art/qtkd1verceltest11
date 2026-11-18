import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
env_path = ROOT_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

HOST = os.getenv("HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "3000"))

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")
# Resolve upload directory
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")

# Resolve upload directory
UPLOAD_PATH = Path(UPLOAD_DIR)

if not UPLOAD_PATH.is_absolute():
    UPLOAD_PATH = (ROOT_DIR / UPLOAD_PATH).resolve()

UPLOAD_PATH.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

SESSION_CLEANUP_TTL_SECONDS = int(os.getenv("SESSION_CLEANUP_TTL_SECONDS", "86400"))
