"""
Configuration Settings for Smart Traffic Management System Backend.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env file if available
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# App Configuration
APP_NAME = "Agentic AI Smart Traffic Management System"
VERSION = "2.0.0"
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))

# Database Configuration (PostgreSQL primary with SQLite fallback)
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "smart_traffic")

DEFAULT_PG_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
SQLITE_URL = f"sqlite:///{BASE_DIR}/database/traffic_app.db"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_PG_URL)

# Ensure database directory exists
db_dir = BASE_DIR / "database"
db_dir.mkdir(parents=True, exist_ok=True)

# Vision / YOLOv8 Settings
YOLO_MODEL_NAME = os.getenv("YOLO_MODEL_NAME", "yolov8n.pt")
DETECTION_CONFIDENCE = float(os.getenv("DETECTION_CONFIDENCE", "0.35"))

# LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini/gemini-1.5-flash")

def get_llm():
    """
    Returns a configured LLM object for CrewAI or None for deterministic fallback.
    """
    if GEMINI_API_KEY and GEMINI_API_KEY not in ("your_gemini_api_key_here", ""):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            model_name = LLM_MODEL.replace("gemini/", "")
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=GEMINI_API_KEY,
                temperature=0.3
            )
        except Exception as e:
            print(f"[Config Warning] Failed to initialize Gemini LLM: {e}. Using deterministic reasoning engine.")
            return None
    elif OPENAI_API_KEY and OPENAI_API_KEY not in ("your_openai_api_key_here", ""):
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY, temperature=0.3)
        except Exception as e:
            print(f"[Config Warning] Failed to initialize OpenAI LLM: {e}. Using deterministic reasoning engine.")
            return None
    return None
