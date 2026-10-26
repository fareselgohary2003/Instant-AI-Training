import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "AI Task Agent"
APP_VERSION = "1.0.0"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USERNAME)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# CORS origins for development and deployment
DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
]

_env_cors = os.getenv("CORS_ORIGINS", "")
if _env_cors:
    CORS_ORIGINS = [origin.strip() for origin in _env_cors.split(",") if origin.strip()]
else:
    CORS_ORIGINS = DEFAULT_CORS_ORIGINS


def validate_config() -> None:
    """Validate core required configurations."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing. Add it to your .env file.")
    if not GROQ_MODEL:
        raise ValueError("GROQ_MODEL is missing. Add it to your .env file.")


def get_settings_status() -> dict[str, Any]:
    """Return a safe summary of configured services without exposing secrets."""
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "llm_provider": "Groq",
        "llm_model": GROQ_MODEL or "Not configured",
        "groq_configured": bool(GROQ_API_KEY),
        "smtp_configured": bool(SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD),
        "smtp_host": SMTP_HOST or "Not configured",
        "sender_email": SENDER_EMAIL or "Not configured",
        "search_configured": bool(TAVILY_API_KEY),
        "search_provider": "Tavily (Direct API)" if TAVILY_API_KEY else "DuckDuckGo Fallback",
        "database": "SQLite (ai_task_agent.db)",
        "cors_origins": CORS_ORIGINS,
    }
