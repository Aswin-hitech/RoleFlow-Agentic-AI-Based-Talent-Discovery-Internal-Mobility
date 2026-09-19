"""OpenAI-compatible client for gpt-oss-120b."""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME") or "gpt-oss-120b"
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT") or "You are a helpful, concise assistant."
TEMPERATURE = float(os.getenv("TEMPERATURE") or 0.7)

_client = None


class LLMError(RuntimeError):
    """Raised when the model provider cannot serve a request."""


def get_client():
    global _client
    if _client is None:
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if not api_key:
            raise LLMError(
                "OPENAI_API_KEY is not set. Add your key to backend/.env and restart the server."
            )
        _client = OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL") or None)
    return _client


def stream_chat(messages):
    """Yield response text chunks for `messages` (a list of {role, content})."""
    client = get_client()
    try:
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, *messages],
            temperature=TEMPERATURE,
            stream=True,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            text = chunk.choices[0].delta.content
            if text:
                yield text
    except LLMError:
        raise
    except Exception as exc:
        raise LLMError(f"{type(exc).__name__}: {exc}") from exc
