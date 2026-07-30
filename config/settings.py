"""
Configuration Settings for Smart Traffic Management System.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if available
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Try .env in current working directory
    load_dotenv()

# App Configuration
APP_NAME = "AI Smart Traffic Management System"
VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", 8000))

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/database/traffic_app.db")

# Ensure database directory exists
db_dir = BASE_DIR / "database"
db_dir.mkdir(parents=True, exist_ok=True)

# LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini/gemini-1.5-flash")

def get_llm():
    """
    Returns a configured CrewAI LLM object or None for deterministic agent fallback.
    """
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            # Use gemini-1.5-flash by default or specified model
            model_name = LLM_MODEL.replace("gemini/", "")
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=GEMINI_API_KEY,
                temperature=0.3
            )
        except Exception as e:
            print(f"[Warning] Failed to initialize Gemini LLM: {e}. Falling back to Rule-Engine mode.")
            return None
    return None
