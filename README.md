# Elementary school chatbot API

FastAPI service that speaks to children in **Persian** (Farsi) with a fixed **teacher** persona (ages 7–10). It forwards requests to [AvalAI](https://api.avalai.ir) `/v1/responses` and injects a server-side system prompt so behavior stays consistent.

## Why an API?

Yes—**a small backend API is the right approach** for a children’s web app: the AvalAI **API key stays on the server**, you can add auth/rate limits/logging later, and the frontend only calls your URL.

## Setup

```bash
cd serendipity
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set AVALAI_API_KEY
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: `GET http://localhost:8000/health`
- Bots list: `GET http://localhost:8000/v1/bots`
- Assess: `POST http://localhost:8000/v1/bots/assess`
- Chat bots: `POST http://localhost:8000/v1/bots/{teacher|story}/chat`
- Legacy: `POST /v1/chat/completions`, `POST /v1/assess`

## Request shape (OpenAI-compatible client API)

Your app still posts to `/v1/chat/completions`; the server maps that to AvalAI Responses (`instructions` + `input`). Default model is `deepseek-v4-flash` (`DEFAULT_MODEL`).

```json
{
  "model": "deepseek-v4-flash",
  "messages": [
    { "role": "user", "content": "سلام!" }
  ]
}
```

**Note:** Client `system` messages are ignored so the teacher persona cannot be overridden from the client.

## Security

- Rotate any API key that was exposed in chat or version control; use only `AVALAI_API_KEY` in `.env` on the server.
- Before production, restrict CORS (`allow_origins`) to your real web app origin instead of `*`.
