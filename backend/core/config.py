import os
import socket
from datetime import timedelta
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _format_postgres_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _database_url() -> str:
    raw = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://roleflow:roleflow@localhost:5432/roleflow",
    )
    # If explicitly postgres, probe connection quickly
    if "postgres" in raw:
        try:
            parsed = urlparse(raw.replace("+psycopg", ""))
            host = parsed.hostname or "localhost"
            port = parsed.port or 5432
            with socket.create_connection((host, port), timeout=0.5):
                return _format_postgres_url(raw)
        except OSError:
            # Fallback to local SQLite so the app starts without crashing (§50)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "roleflow.db")
            return f"sqlite:///{db_path}"
    return raw


class Config:
    """All settings come from the environment — see backend/.env.example."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    DEBUG = _bool("FLASK_DEBUG", "1")
    API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # Database
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = (
        {"pool_pre_ping": True, "connect_args": {"connect_timeout": 3}}
        if "postgresql" in SQLALCHEMY_DATABASE_URI
        else {}
    )
    PGVECTOR_DIM = int(os.getenv("PGVECTOR_DIM", "768"))

    # MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "roleflow")

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-secret-key-roleflow")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "30"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "14"))
    )

    # OAuth (optional)
    OAUTH_GOOGLE_CLIENT_ID = os.getenv("OAUTH_GOOGLE_CLIENT_ID", "")
    OAUTH_GOOGLE_CLIENT_SECRET = os.getenv("OAUTH_GOOGLE_CLIENT_SECRET", "")
    OAUTH_GITHUB_CLIENT_ID = os.getenv("OAUTH_GITHUB_CLIENT_ID", "")
    OAUTH_GITHUB_CLIENT_SECRET = os.getenv("OAUTH_GITHUB_CLIENT_SECRET", "")

    # LLM — GPT-OSS-120B behind an OpenAI-compatible endpoint
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai-compatible")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-oss-120b")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))

    # Embeddings — BGE-base / Sentence-BERT
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
    EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "768"))

    # Demo
    DEMO_USER_PASSWORD = os.getenv("DEMO_USER_PASSWORD", "demo1234")
