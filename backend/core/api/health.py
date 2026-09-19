"""Health API endpoint (§4, §50).

Statuses: Connected | Unavailable | Configured.
Instructions if unavailable:
- Start PostgreSQL
- Start MongoDB
- Start Redis
- Check LLM endpoint
"""

import socket
from urllib.parse import urlparse
from flask import Blueprint, current_app, jsonify

health_bp = Blueprint("health", __name__)


def _check_postgres() -> str:
    url = current_app.config["SQLALCHEMY_DATABASE_URI"]
    if "sqlite" in url:
        return "Connected"
    try:
        parsed = urlparse(url.replace("+psycopg", ""))
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        with socket.create_connection((host, port), timeout=0.5):
            return "Connected"
    except Exception:
        return "Unavailable"


def _check_redis() -> str:
    url = current_app.config["REDIS_URL"]
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        with socket.create_connection((host, port), timeout=0.5):
            return "Connected"
    except Exception:
        return "Unavailable"


def _check_mongodb() -> str:
    url = current_app.config["MONGODB_URI"]
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 27017
        with socket.create_connection((host, port), timeout=0.5):
            return "Connected"
    except Exception:
        return "Unavailable"


def _check_llm() -> str:
    url = current_app.config["LLM_BASE_URL"]
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 11434
        with socket.create_connection((host, port), timeout=0.5):
            return "Connected"
    except Exception:
        return "Configured"  # configured via env, fallback active


@health_bp.get("")
def health():
    services = {
        "postgres": _check_postgres(),
        "redis": _check_redis(),
        "mongodb": _check_mongodb(),
        "llm": _check_llm(),
    }

    instructions = {
        "postgres": "Start PostgreSQL" if services["postgres"] == "Unavailable" else "Running",
        "redis": "Start Redis" if services["redis"] == "Unavailable" else "Running",
        "mongodb": "Start MongoDB" if services["mongodb"] == "Unavailable" else "Running",
        "llm": "Check LLM endpoint" if services["llm"] == "Unavailable" else "Running",
    }

    return jsonify(
        status="ok",
        services=services,
        instructions=instructions,
        llm_model=current_app.config["LLM_MODEL"],
        embedding_model=current_app.config["EMBEDDING_MODEL"],
    )
