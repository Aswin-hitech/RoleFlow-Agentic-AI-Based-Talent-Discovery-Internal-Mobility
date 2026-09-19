"""Flask API for the chatbot."""

import json
import os

from flask import Flask, Response, jsonify, request

from llm import MODEL_NAME, LLMError, stream_chat

app = Flask(__name__)

MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES") or 40)
MAX_MESSAGE_CHARS = int(os.getenv("MAX_MESSAGE_CHARS") or 8000)


class BadRequest(ValueError):
    pass


def parse_messages(raw):
    if not isinstance(raw, list) or not raw:
        raise BadRequest("`messages` must be a non-empty list.")

    messages = []
    for item in raw:
        if not isinstance(item, dict):
            raise BadRequest("Every message must be an object.")
        role = item.get("role")
        content = item.get("content")
        if role not in ("user", "assistant"):
            raise BadRequest("Message `role` must be 'user' or 'assistant'.")
        if not isinstance(content, str) or not content.strip():
            raise BadRequest("Message `content` must be a non-empty string.")
        messages.append({"role": role, "content": content[:MAX_MESSAGE_CHARS]})

    if messages[-1]["role"] != "user":
        raise BadRequest("The last message must be from the user.")

    return messages[-MAX_HISTORY_MESSAGES:]


def sse(payload):
    return f"data: {json.dumps(payload)}\n\n"


def sse_events(messages):
    try:
        for token in stream_chat(messages):
            yield sse({"delta": token})
    except LLMError as exc:
        app.logger.error("LLM request failed: %s", exc)
        yield sse({"error": str(exc)})
    yield sse({"done": True})


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "model": MODEL_NAME})


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Request body must be JSON."}), 400

    try:
        messages = parse_messages(payload.get("messages"))
    except BadRequest as exc:
        return jsonify({"error": str(exc)}), 400

    return Response(
        sse_events(messages),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT") or 5000),
        debug=(os.getenv("FLASK_DEBUG") or "1") == "1",
        threaded=True,
    )
