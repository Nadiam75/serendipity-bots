# Elementary school chatbot API

FastAPI service for a Persian elementary learning app (ages 7–10). It exposes chat bots, answer assessment, exercise generation, and fun facts. All AI calls go through [AvalAI](https://api.avalai.ir); the API key stays on the server.

## Setup

```bash
cd serendipity
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Set AVALAI_API_KEY in .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: `GET http://localhost:8000/health`
- Interactive docs: `http://localhost:8000/docs`
- **Full API reference (request/response samples):** [docs/API.md](docs/API.md)
- **Deploy to VPS:** [docs/DEPLOY.md](docs/DEPLOY.md)

## Endpoints (summary)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness |
| `GET` | `/v1/contracts` | Question types & examples (`contracts.json`) |
| `GET` | `/v1/bots` | List bots |
| `POST` | `/v1/bots/teacher/chat` | Teacher chat |
| `POST` | `/v1/bots/story/chat` | Story chat |
| `POST` | `/v1/bots/assess` | Assess child answer |
| `POST` | `/v1/bots/generate-exercises` | Generate similar exercises |
| `POST` | `/v1/bots/fun-fact` | Fun fact from interests |

Legacy: `POST /v1/chat/completions`, `POST /v1/assess`, `POST /v1/fun-fact`

## Contracts

Question shapes (`mcq_single`, `mcq_multi`, `open_question`, `image_mcq`) are defined in [`contracts.json`](contracts.json). The API serves them at `GET /v1/contracts` and uses them in assess/generate request and response bodies.

## Security

- Keep `AVALAI_API_KEY` only in `.env` on the server.
- Restrict CORS (`allow_origins`) to your production web app origin before go-live.
