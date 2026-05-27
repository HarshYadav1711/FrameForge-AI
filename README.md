# FrameForge AI

Local-first AI video automation: narration audio + script → transcribed, scene-segmented, subtitled MP4.

## Architecture

| Layer | Stack | Role |
|-------|-------|------|
| **Frontend** | Next.js (App Router), TypeScript, Tailwind, shadcn/ui | Landing shell + studio UI |
| **Backend** | FastAPI, Python 3.11+ | REST API + async pipeline |
| **AI** | Faster-Whisper, Ollama (optional Gemini) | Transcribe + segment |
| **Video** | MoviePy, FFmpeg | Compose + render |

**Modular monolith** — one deployable API, one web app. Pipeline logic lives in `services/`; HTTP stays thin in `api/routes/`. Jobs persist as folders under `backend/storage/jobs/` (no database until you need multi-instance coordination).

```
frontend/src/
  app/              # Routes: landing (/), studio (/studio)
  components/       # layout, landing, studio, common
  lib/api/          # Typed API modules (jobs, health)
  lib/http/         # Shared fetch client + ApiError
  hooks/            # useAsync and domain hooks
  config/           # env

backend/app/
  api/routes/       # health, jobs
  pipeline/         # orchestrator
  services/         # transcribe, segment, visuals, subtitles, render
  core/             # logging, exceptions, health checks
  models/           # Pydantic schemas
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- FFmpeg on PATH
- Ollama (optional): `ollama pull llama3.2`

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
pip install ruff                # optional, for lint/format
copy .env.example .env
python run.py
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

| URL | Purpose |
|-----|---------|
| http://localhost:3000 | Landing |
| http://localhost:3000/studio | Video studio |
| http://localhost:8000/docs | OpenAPI |
| http://localhost:8000/api/v1/health | Service health |

## Health endpoints

| Endpoint | Use |
|----------|-----|
| `GET /api/v1/health` | Version, model config |
| `GET /api/v1/health/live` | Liveness (process up) |
| `GET /api/v1/health/ready` | Readiness (storage writable) |

## Lint & format

```bash
# Frontend
cd frontend && npm run lint && npm run format:check && npm run typecheck

# Backend
cd backend && ruff check app && ruff format --check app
```

## Environment

See `backend/.env.example` and `frontend/.env.example`.

## License

MIT
