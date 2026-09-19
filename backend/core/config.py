import logging
import os
import socket
from datetime import timedelta
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _bool(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _format_postgres_url(url: str) -> str:
    has_psycopg3 = False
    try:
        import psycopg
        has_psycopg3 = True
    except ImportError:
        pass

    driver = "postgresql+psycopg://" if has_psycopg3 else "postgresql+psycopg2://"
    if url.startswith("postgres://"):
        return url.replace("postgres://", driver, 1)
    elif url.startswith("postgresql://") and not ("+psycopg" in url or "+psycopg2" in url):
        return url.replace("postgresql://", driver, 1)
    return url


def _database_url() -> str:
    raw = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://roleflow:roleflow@localhost:5432/roleflow",
    )
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sqlite_fallback = f"sqlite:///{os.path.join(base_dir, 'roleflow.db')}"

    # If explicitly postgres, probe connection quickly and verify driver
    if "postgres" in raw:
        try:
            parsed = urlparse(raw.replace("+psycopg", "").replace("+psycopg2", ""))
            host = parsed.hostname or "localhost"
            port = parsed.port or 5432
            # Quick probe
            with socket.create_connection((host, port), timeout=0.5):
                formatted = _format_postgres_url(raw)
                # Verify DBAPI driver can be imported
                if "+psycopg://" in formatted:
                    import psycopg
                else:
                    import psycopg2
                return formatted
        except Exception:
            # Fallback to local SQLite so the app starts without crashing (§50)
            return sqlite_fallback
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

    # Environment & Security Guards
    ROLEFLOW_ENV = os.getenv("ROLEFLOW_ENV", os.getenv("FLASK_ENV", "development")).lower()
    IS_PRODUCTION = ROLEFLOW_ENV == "production"
    ALLOW_DEMO_USERS = _bool("ALLOW_DEMO_USERS", "0" if IS_PRODUCTION else "1")
    RATE_LIMIT_ENABLED = _bool("RATE_LIMIT_ENABLED", "1")

    # Demo
    DEMO_USER_PASSWORD = os.getenv("DEMO_USER_PASSWORD", "demo1234")

    @classmethod
    def validate_production_security(cls):
        """Validate security settings when running in production."""
        validate_production_security(cls)


def validate_production_security(conf=None):
    """Validate security settings when running in production.
    
    Raises:
        RuntimeError: If security requirements are not met in production.
    """
    if conf is None:
        env = Config.ROLEFLOW_ENV
        jwt_key = Config.JWT_SECRET_KEY
        secret_key = Config.SECRET_KEY
    elif isinstance(conf, dict):
        env = str(conf.get("ROLEFLOW_ENV", "development")).lower()
        jwt_key = str(conf.get("JWT_SECRET_KEY", ""))
        secret_key = str(conf.get("SECRET_KEY", "default-app-secret-key-prod-ok"))
    else:
        env = str(getattr(conf, "ROLEFLOW_ENV", "development")).lower()
        jwt_key = str(getattr(conf, "JWT_SECRET_KEY", ""))
        secret_key = str(getattr(conf, "SECRET_KEY", "default-app-secret-key-prod-ok"))

    if env == "production":
        insecure_keys = [
            "change-me-secret-key-roleflow",
            "dev-secret-change-me",
            "roleflow-jwt-insecure-secret-key-change-in-prod",
            "",
        ]
        if jwt_key in insecure_keys or len(jwt_key) < 16:
            raise RuntimeError("Insecure JWT_SECRET_KEY detected in production! A cryptographically secure secret is required.")
        if secret_key in insecure_keys or len(secret_key) < 16:
            raise RuntimeError("Insecure SECRET_KEY detected in production! A cryptographically secure secret is required.")
