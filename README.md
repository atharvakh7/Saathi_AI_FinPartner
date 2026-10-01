# Saathi

Multilingual, voice-first AI financial companion. The full specification is in `SPEC.md`; decisions and deviations are in `ASSUMPTIONS.md`.

```
backend/   FastAPI API, Celery jobs, AI adapters, Alembic migrations, seed data
mobile/    Expo (React Native + TypeScript) app
```

## Local services

Requires Docker Desktop (WSL2 backend on Windows).

```sh
cp backend/.env.example backend/.env      # then fill JWT_SECRET, DATA_ENCRYPTION_KEY, OTP_HMAC_KEY
docker compose -f backend/docker-compose.dev.yml up -d   # reads backend/.env automatically
docker compose -f backend/docker-compose.dev.yml ps
```

| Service | Port | Notes |
|---|---|---|
| Postgres 16 + pgvector | 5432 | user/db `saathi` |
| Redis 7 | 6379 | |
| MinIO (`bitnamilegacy/minio`, dev only) | 9000 (API), 9001 (console) | buckets created on startup |
| Ollama (NVIDIA GPU) | 11434 | `gemma4:e4b-it-qat` + `bge-m3` pulled by `ollama-init` (~7 GB on first run) |

Follow the first model download with `docker compose -f backend/docker-compose.dev.yml logs -f ollama-init`.

## Backend setup

```sh
cd backend
py -3.11 -m venv .venv
.venv/Scripts/pip install -r requirements.txt -r requirements-ml.txt -r requirements-dev.txt
# model files: see backend/ml_models/README.md; Tesseract: winget install UB-Mannheim.TesseractOCR
.venv/Scripts/alembic upgrade head          # create/upgrade the schema
.venv/Scripts/python -m app.seed.seed       # load schemes, glossary, lessons, fraud rules (idempotent)
.venv/Scripts/uvicorn app.main:app --reload # API on http://localhost:8000 (docs at /docs)
.venv/Scripts/python -m app.ai.demo         # check every AI adapter (LLM, embeddings, STT, TTS, OCR, ...)
```

## Deferred work

- [GPU speech-to-text](docs/deferred/gpu-whisper.md): paused in step 7; why, where it got stuck, and how to finish it.
