# Saathi

Multilingual, voice-first AI financial companion. The full specification is in `SPEC.md`; decisions and deviations are in `ASSUMPTIONS.md`; what is done and what is left is in `PROJECT_STATUS.md`.

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
| Ollama (NVIDIA GPU) | 11434 | `bge-m3` embeddings (and `gemma4:e4b-it-qat` if you run the LLM locally), pulled by `ollama-init` |

Follow the first model download with `docker compose -f backend/docker-compose.dev.yml logs -f ollama-init`.

## LLM: local or hosted

The API talks to any OpenAI-compatible endpoint. Two set-ups:

- **Local (needs a GPU with ~6 GB and plenty of RAM):** Ollama `gemma4:e4b-it-qat` — `LLM_BASE_URL=http://localhost:11434/v1`, `LLM_MODEL=gemma4:e4b-it-qat`, `LLM_API_KEY=ollama`.
- **Hosted (laptops that can't hold the model):** Google Gemini — `LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai`, `LLM_MODEL=gemini-flash-latest`, `LLM_FALLBACK_MODELS=gemini-3.8-flash,gemini-3.1-flash-lite`, `LLM_API_KEY=<key from aistudio.google.com/apikey>`, `LLM_TIMEOUT_SEC=25`. Chats are then sent to Google; the privacy notice (v1.1) says so.

Embeddings stay on Ollama (`bge-m3`) either way. On a low-memory machine also set `AI_WARMUP=false` and `TRANSLATE_ON_STARTUP=false`.

## Backend setup

```sh
cd backend
py -3.11 -m venv .venv                      # 3.12 also works
.venv/Scripts/pip install -r requirements.txt -r requirements-ml.txt -r requirements-dev.txt
# model files: see backend/ml_models/README.md; Tesseract: winget install UB-Mannheim.TesseractOCR
.venv/Scripts/alembic upgrade head          # create/upgrade the schema
.venv/Scripts/python -m app.seed.seed       # load schemes, glossary, lessons, fraud rules (idempotent)
.venv/Scripts/uvicorn app.main:app --reload # API on http://localhost:8000 (docs at /docs)
.venv/Scripts/python -m app.ai.demo         # check every AI adapter (LLM, embeddings, STT, TTS, OCR, ...)
```

## Mobile app (Expo)

```
cd mobile
npm install
npx expo start --web    # browser preview at http://localhost:8081 (set EXPO_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1)
npx expo start          # or scan the QR code with the Expo Go app (Android/iOS)
```

For the browser preview, add `http://localhost:8081` to `CORS_ORIGINS` in `backend/.env`. Voice works in the browser (it asks for the microphone). Push notifications need a development build and `EXPO_PUBLIC_EAS_PROJECT_ID` (`npx eas init`); in Expo Go on Android and on the web they appear only in the in-app inbox.

- Phone and PC must be on the same Wi-Fi. For screens that call the API, set `EXPO_PUBLIC_API_BASE_URL` in `mobile/.env` to `http://<your PC's LAN IP>:8000/api/v1` and run the API with `--host 0.0.0.0` (the Android emulator uses `10.0.2.2`).
- Checks: `npm run typecheck`, `npm test`, `npm run check:i18n -- --used`, `npx expo-doctor`.
- Component gallery (development only): open `/dev/gallery` (`npx expo start --web`, or `saathi://dev/gallery` on the phone).

## Background jobs

By default (`CELERY_ENABLED=false`) background work such as memory extraction and insights runs inside the API process, so nothing else needs to run. To use Celery and the daily schedule (insights 08:30, reminders, nightly planner/schemes, purge):

```
# in backend/.env: CELERY_ENABLED=true
cd backend
.venv/Scripts/celery -A app.jobs.celery_app worker --pool=solo -l info   # Windows needs --pool=solo
.venv/Scripts/celery -A app.jobs.celery_app beat -l info
```

Run any job once by hand: `.venv/Scripts/python -m app.jobs.run --list`, then e.g. `.venv/Scripts/python -m app.jobs.run insights.generate_all`.

## Deferred work

- [GPU speech-to-text](docs/deferred/gpu-whisper.md): paused in step 7; why, where it got stuck, and how to finish it.
