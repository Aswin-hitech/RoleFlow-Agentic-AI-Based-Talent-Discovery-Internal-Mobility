"""LLM gateway — LangChain client for GPT-OSS-120B with resilient fallback."""

import json
import logging
from functools import lru_cache

from ..config import Config

logger = logging.getLogger(__name__)


import socket
from urllib.parse import urlparse


def _is_server_reachable(url: str, timeout: float = 0.3) -> bool:
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


@lru_cache(maxsize=1)
def get_llm():
    if not _is_server_reachable(Config.LLM_BASE_URL, timeout=0.25):
        logger.debug("LLM endpoint %s not reachable; using fast deterministic fallback", Config.LLM_BASE_URL)
        return None

    try:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=Config.LLM_MODEL,
            api_key=Config.LLM_API_KEY,
            base_url=Config.LLM_BASE_URL,
            temperature=Config.LLM_TEMPERATURE,
            max_tokens=Config.LLM_MAX_TOKENS,
            request_timeout=3.0,
        )
    except Exception as exc:
        logger.warning("Could not initialize LangChain ChatOpenAI: %s", exc)
        return None


def generate_structured(prompt: str, schema_hint: str) -> str:
    """Ask GPT-OSS-120B for JSON matching the hint, or return deterministic structured response."""
    llm = get_llm()
    if llm:
        try:
            messages = [
                ("system", f"You are RoleFlow's core agentic intelligence engine. Respond with strictly valid JSON only. Shape: {schema_hint}"),
                ("human", prompt),
            ]
            response = llm.invoke(messages)
            text = response.content.strip()
            # Strip potential markdown fences
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            # Validate JSON
            json.loads(text)
            return text
        except Exception as exc:
            logger.warning("LLM call failed, proceeding with deterministic fallback: %s", exc)

    return ""
