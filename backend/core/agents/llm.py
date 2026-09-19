"""LLM gateway — Swappable LangChain client supporting Groq, OpenAI, Ollama, vLLM, Azure, and Mock modes."""

import json
import logging
import socket
from functools import lru_cache
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from ..config import Config

logger = logging.getLogger(__name__)


def _is_server_reachable(url: str, timeout: float = 0.25) -> bool:
    """Fast probe to determine if remote LLM socket endpoint is reachable."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def get_llm_info() -> Dict[str, Any]:
    """Retrieve metadata about the currently configured LLM provider."""
    provider = (Config.LLM_PROVIDER or "openai-compatible").lower()
    is_mock = provider in {"mock", "none", "disabled", "offline"}
    base_url = Config.LLM_BASE_URL
    is_live = not is_mock and _is_server_reachable(base_url, timeout=0.25)

    return {
        "provider": provider,
        "model": Config.LLM_MODEL,
        "base_url": base_url,
        "is_mock": is_mock,
        "is_reachable": is_live,
        "temperature": Config.LLM_TEMPERATURE,
    }


@lru_cache(maxsize=1)
def get_llm():
    """Factory creating an authenticated LangChain client based on Config.LLM_PROVIDER.
    
    Supports:
      - 'mock': deterministic offline fallback (instant, zero-network).
      - 'ollama': local Ollama instance (http://localhost:11434/v1).
      - 'groq': Groq Cloud high-performance inference (https://api.groq.com/openai/v1).
      - 'openai': official OpenAI endpoint (https://api.openai.com/v1).
      - 'vllm': self-hosted vLLM API server.
      - 'azure': Azure OpenAI endpoint.
    """
    provider = (Config.LLM_PROVIDER or "openai-compatible").lower()

    # 1. Explicit Mock / Offline mode for testing and local deterministic execution
    if provider in {"mock", "none", "disabled", "offline"}:
        logger.debug("LLM provider set to '%s'; using deterministic agentic fallback", provider)
        return None

    # 2. Resolve base URL and API key defaults if not explicitly set
    base_url = Config.LLM_BASE_URL
    api_key = Config.LLM_API_KEY or "none"
    model = Config.LLM_MODEL

    if provider == "groq" and ("localhost" in base_url or not base_url):
        base_url = "https://api.groq.com/openai/v1"
    elif provider == "openai" and ("localhost" in base_url or not base_url):
        base_url = "https://api.openai.com/v1"

    # 3. Fast pre-flight socket probe (0.25s) to avoid client timeouts if host is offline
    if not _is_server_reachable(base_url, timeout=0.25):
        logger.debug("LLM endpoint %s not reachable; using fast deterministic fallback", base_url)
        return None

    try:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=Config.LLM_TEMPERATURE,
            max_tokens=Config.LLM_MAX_TOKENS,
            request_timeout=4.0,
        )
    except Exception as exc:
        logger.warning("Could not initialize LangChain ChatOpenAI for provider '%s': %s", provider, exc)
        return None


def generate_structured(prompt: str, schema_hint: str) -> str:
    """Ask configured LLM for JSON matching the hint, or return empty string for deterministic fallback."""
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
                parts = text.split("```")
                if len(parts) >= 2:
                    text = parts[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            # Validate JSON syntax
            json.loads(text)
            return text
        except Exception as exc:
            logger.warning("LLM call failed, proceeding with deterministic fallback: %s", exc)

    return ""
