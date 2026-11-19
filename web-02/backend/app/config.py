from pathlib import Path
import os
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")
DATA_DIR = Path(os.getenv("WEB02_DATA_DIR", str(BASE_DIR / "var"))).resolve()
UPLOAD_DIR = DATA_DIR / "uploads"
ARTIFACT_DIR = DATA_DIR / "artifacts"
DATABASE_URL = os.getenv("WEB02_DATABASE_URL", f"sqlite:///{DATA_DIR / 'web02.sqlite3'}")
DA_AGENT_DIR = Path(os.getenv("DA_AGENT_DIR", str(BASE_DIR.parent / "DA-Agent-drive"))).resolve()
SECRET_KEY = os.getenv("WEB02_SECRET_KEY", "change-this-secret-before-deployment")
COOKIE_SECURE = os.getenv("WEB02_COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}
MAX_FILE_BYTES = int(os.getenv("WEB02_MAX_FILE_BYTES", str(10 * 1024 * 1024)))
MAX_ASSIGNMENT_BYTES = int(os.getenv("WEB02_MAX_ASSIGNMENT_BYTES", str(20 * 1024 * 1024)))
ALLOWED_SUFFIXES = {".csv", ".xlsx"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
