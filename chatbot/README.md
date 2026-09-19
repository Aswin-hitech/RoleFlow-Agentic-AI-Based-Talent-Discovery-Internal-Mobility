# Chatbot

A basic streaming chatbot: a React (Vite) frontend, a Flask backend, and an LLM served over
any OpenAI-compatible API. Defaults to **gpt-oss-120b**.

Replies stream token by token over Server-Sent Events, so text appears as the model produces it.

## Layout

```
chatbot/
├── backend/
│   ├── app.py            Flask API: POST /api/chat (SSE), GET /api/health
│   ├── llm.py            OpenAI-compatible client + streaming
│   ├── requirements.txt
│   ├── .env              your config (git-ignored)
│   └── .env.example      documented template
└── frontend/
    ├── index.html
    ├── vite.config.js    dev server + /api proxy to Flask
    ├── package.json
    └── src/
        ├── main.jsx
        ├── App.jsx           chat state and layout
        ├── api.js            SSE stream reader
        ├── styles.css
        └── components/
            ├── ChatInput.jsx
            └── MessageBubble.jsx
```

## 1. Configure the backend

Open `backend/.env` and set two values — your API key, and the base URL of the host serving
your model:

```ini
OPENAI_API_KEY=your-key-here
OPENAI_BASE_URL=https://api.groq.com/openai/v1
MODEL_NAME=openai/gpt-oss-120b
```

`OPENAI_BASE_URL` is a base URL only — do **not** append `/chat/completions`.

| Host | `OPENAI_BASE_URL` | `MODEL_NAME` |
| --- | --- | --- |
| Groq | `https://api.groq.com/openai/v1` | `openai/gpt-oss-120b` |
| Ollama (local) | `http://localhost:11434/v1` | `gpt-oss:120b` |
| vLLM (local) | `http://localhost:8000/v1` | as served |
| OpenRouter | `https://openrouter.ai/api/v1` | `openai/gpt-oss-120b` |
| Together | `https://api.together.xyz/v1` | `openai/gpt-oss-120b` |
| Cerebras | `https://api.cerebras.ai/v1` | `gpt-oss-120b` |

For Ollama, pull the model once first: `ollama pull gpt-oss:120b`, and set `OPENAI_API_KEY`
to any non-empty string (Ollama ignores it).

## 2. Run the backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
python app.py
```

Serves on http://127.0.0.1:5000. Check it with http://127.0.0.1:5000/api/health.

## 3. Run the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the printed URL (http://localhost:5173 by default). Vite proxies `/api` to the Flask
server, so no CORS setup is needed. Keep both terminals running.

For a production build: `npm run build`, then serve `frontend/dist/`.

## API

**`POST /api/chat`**

```json
{ "messages": [{ "role": "user", "content": "Hello" }] }
```

Responds with `text/event-stream`:

```
data: {"delta": "Hello"}
data: {"delta": " there"}
data: {"done": true}
```

A failure mid-stream arrives as `data: {"error": "..."}` followed by `{"done": true}`.
Malformed requests get a plain `400` with `{"error": "..."}`.

## Configuration

All optional except `OPENAI_API_KEY` (see `backend/.env.example`):

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | — | required |
| `OPENAI_BASE_URL` | OpenAI | endpoint of your model host |
| `MODEL_NAME` | `gpt-oss-120b` | model id |
| `TEMPERATURE` | `0.7` | sampling temperature |
| `SYSTEM_PROMPT` | helpful assistant | system message |
| `PORT` | `5000` | Flask port |
| `FLASK_DEBUG` | `1` | `0` to disable the reloader |
| `MAX_HISTORY_MESSAGES` | `40` | turns of history sent per request |
| `MAX_MESSAGE_CHARS` | `8000` | per-message truncation limit |

## Notes

- Conversation state lives in React only. The full history is resent each turn and trimmed to
  `MAX_HISTORY_MESSAGES`; nothing is persisted server-side.
- The Flask dev server is for local development. For production use a WSGI server that supports
  streaming (e.g. gunicorn with a threaded or gevent worker) and set `FLASK_DEBUG=0`.
