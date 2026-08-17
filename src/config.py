import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent

def resolve_path(env_val: str, default_val: str) -> Path:
    val = os.getenv(env_val, default_val)
    path = Path(val)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path

DB_PATH = resolve_path("DATABASE_PATH", "data/nifty100.db")
OUTPUT_DIR = resolve_path("OUTPUT_DIR", "output")
REPORTS_DIR = resolve_path("REPORTS_DIR", "reports")
DATA_DIR = resolve_path("DATA_DIR", "Dataset")
SUPPLEMENTARY_DIR = resolve_path("SUPPLEMENTARY_DIR", "Dataset/supporting datasets")
LOG_FILE = resolve_path("LOG_FILE", "output/etl.log")

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8501"))

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
if LOG_FILE.parent:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)