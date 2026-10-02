# Saathi — project status

_Last updated: 2026-10-02_

Saathi is a multilingual (English, Hindi, Marathi, Tamil) AI financial companion built for the Paytm Build for India AI Hackathon. It is built from a 31-step build specification (§10 "Build order"), one step at a time and in order: backend first (steps 1–18), then the mobile app (steps 19–31).

**Where we are: all 31 steps done.** The backend is complete. The mobile app has its skeleton, onboarding, tab shell, profile and settings, finance, Goals, Plan / Risk Report / Emergency Fund, the Saathi chat with voice, Learn, Scheme Scout, Fraud Shield, insights and notifications, and a UI pass matching the wireframe. The final integration pass (step 31) found no problems across 189 screen visits.

Related files:
- [ASSUMPTIONS.md](ASSUMPTIONS.md) — every decision and deviation from the spec, step by step.
- [README.md](README.md) — setup and run commands.
- [docs/deferred/](docs/deferred/) — work that is intentionally paused.

---

## Stack

| Part | Technology |
|---|---|
| API | FastAPI, async SQLAlchemy, Alembic, Postgres 16 with pgvector, Redis, MinIO |
| AI | LLM: Google Gemini via its OpenAI-compatible API on this laptop (`gemini-flash-latest` + fallbacks); local Ollama `gemma4:e4b-it-qat` on machines that can hold it. Embeddings: Ollama `bge-m3`. Whisper via pywhispercpp (speech-to-text, CPU, `small`), Piper (text-to-speech), Tesseract (OCR) |
| Background jobs | Celery and Celery Beat (Redis broker). On Windows this needs `--pool=solo`. With `CELERY_ENABLED=false`, jobs run inline in the API process. |
| Mobile | Minimal & clean UI; tabs Home · Services · Saathi (mic) · Goals · Profile. Expo SDK 57, React Native 0.86, React 19, TypeScript 6, Expo Router (typed routes), Zustand, React Query, react-hook-form with zod, i18next, axios. Runs in **Expo Go** (no native build). |
| Local services | `backend/docker-compose.dev.yml`: postgres, redis, minio, ollama (Docker Desktop on WSL2) |

---

## Completed

### Backend: steps 1–18 (complete)

| # | Step | Notes |
|---|---|---|
| 1 | Repo and local services | Docker compose with healthchecks |
| 2 | Backend skeleton | Error envelope, `/health`, Redis rate limiter, JWT and crypto utilities, PII redactor |
| 3 | Database schema | One Alembic migration for every table in §6 |
| 4 | Seed data | 28 schemes, 30 glossary terms, 12 lessons, fraud rules, goal templates. Seeding is idempotent. |
| 5 | Auth | OTP request and verify, refresh, logout, `/me`. OTP is printed to the API console in dev (`OTP_PROVIDER=console`). |
| 6 | Users | Profile, confidence assessment, consents, onboarding, device tokens, notification settings, data export, account delete |
| 7 | AI adapters | LLM, embeddings, STT, TTS, OCR, language detection. The scam classifier is disabled (no trained model), so Fraud Shield uses rules only. |
| 8 | Finance | Transactions, debts, summary, natural-language transaction parsing |
| 9 | Goals | Goals, contributions, projection, templates |
| 10 | Planner | Forecast, budget, emergency fund, risk score, overview, history |
| 11 | Learn | Glossary, term detection, translations, lessons, XP and streaks, video presigned URLs |
| 12 | Memory | Fact extraction, dedupe, retrieval, summarization, `/memory` endpoints |
| 13 | Schemes | Eligibility rules, questions, matching, translated details, tracking |
| 14 | Fraud | Rules pipeline, critical-rule score floor, LLM explanation, reports |
| 15 | Voice | `/chat/transcribe`, `/chat/tts`, TTS cache. Marathi is decoded with the Hindi model (better accuracy). |
| 16 | Chat orchestrator | Intent router, tools (jargon, fraud, schemes, budget, transaction and goal confirmation flows, distress), guardrails |
| 17 | Insights and notifications | Rules I01–I09, Expo push, quiet hours 22:00–07:00 IST, max 3 pushes per day, Celery Beat schedule (IST) |
| 18 | Admin API | Role-guarded CRUD, cache invalidation on writes |

Verification: the full backend test sweep passed (16 suites, 613 checks).

### Mobile: steps 19–31 (complete)

| # | Step | Notes |
|---|---|---|
| 19 | Mobile skeleton | Theme tokens, fonts (Poppins, Inter, Noto Devanagari, Noto Tamil), i18n with all 395 keys in en/hi/mr/ta, axios client with single-flight token refresh, stores, shared components, 7 mascot poses |
| 20 | Onboarding S01–S09 | Welcome, intro, phone, OTP, consent, privacy, profile, confidence, goals |
| 21 | Tabs, profile and settings S35–S40 | Five tabs (Home, Plan, centre Saathi mic, Learn, Profile), edit profile, language, notifications, privacy and data (export, delete account), memory |
| 22 | Finance UI S14–S16, Home metrics S10 | Transactions list (month, filter, infinite scroll), add/edit with "tell me in words" fill, debts with mark-paid, Home quick summary + debt/goal cards. Verified against a mocked API and the live API. |
| 23 | Goals UI S17–S19 + wireframe UI pass | Goals list (Active/Completed), detail (ring, projection, add/withdraw, pause, history), create/edit; new splash, 3-slide intro, Home with Top Goals and Financial-Twin tiles |
| 24 | Plan S20, Emergency Fund S21, Risk Report S12, Home risk + EF cards | Income planner (bars, outlook chart, budget, recommended savings), EF setup (3–12 months), risk breakdown with tips and 90-day history; fixed gauge colour bands |
| 25 | Saathi chat S22 (text), TermSheet, ChatCards | Chat with greeting, chips, tappable terms, cards, transaction confirmation, history; LLM switched to Gemini with fallback models; fixed list scrolling on web |
| 26 | Voice in chat | Full-screen voice mode (wireframe), record → Whisper → reply → spoken (server voice or on-device, Tamil on-device), speaker on every answer; privacy notice 1.1 with re-consent |
| 27 | Learn S32–S34 | Stats (XP, level, streak), term search + popular terms, lessons; term page (example, analogy, listen, related, feedback); lesson with Mark complete (+XP) |
| 28 | Scheme Scout S23–S27 | Profile match, eligibility questions, matches (incl. not-qualified reasons), category list, scheme detail (rules, steps, documents, tracking); translated on first open |
| 29 | Fraud Shield S28–S31 | Paste or screenshot, verdict banner, translated red flags, report, 1930 helpline, history; Home "Services" shortcuts |
| 30 | Insights S11, Notifications S13, push | Insight feed with filters, inbox, bell with unread count, latest insights on Home, push registration (needs a dev build + EAS project) |
| 31 | Final integration pass | Not-found page; sweep of every route × 4 languages, empty account and offline API: no problems |

Verification: `tsc` clean, 48 Jest tests passing (12 suites), i18n check passing (776 keys), expo-doctor 21/21, web end-to-end tests (onboarding 26/26, step 21 35/35, step 22 40/40 against a mocked API). The app has also been run on the Android emulator.

### Dev environment
- The Android emulator is set up on the dev laptop (command-line SDK, no Android Studio). See **How to run** below.

---

## Still to do

### Mobile
All 31 steps are done.

### Open items outside the step list
- **`SPEC.md` is missing** from the repo. Steps from 22 on are built from ASSUMPTIONS, the API and the UI wireframes; recover the spec to re-check them.
- **This dev laptop (GTX 1650 4 GB, 7.3 GB RAM):** API runs on Python 3.12 with `AI_WARMUP=false`; Whisper small (CPU) and Piper en/hi/mr are installed; Tesseract is not (screenshot OCR unavailable). App previewed as Expo web on http://localhost:8081.
- **Privacy notice 1.1** discloses Gemini; existing users re-accept once. The text is a draft for legal review.
- **UI refresh done (after step 31):** minimal & clean design system, tab bar Home · Services · Saathi · Goals · Profile, real 3D mascot (8 poses) and new app icon / splash. Higher-resolution mascot exports would sharpen large sizes.
- **GPU Whisper (deferred):** speech-to-text runs on CPU. A CUDA build was paused; the resume notes are in [docs/deferred/gpu-whisper.md](docs/deferred/gpu-whisper.md).
- **Push notifications:** the app registers devices, but `EXPO_PUBLIC_EAS_PROJECT_ID` in `mobile/.env` is empty and Expo Go on Android has no remote push. Run `npx eas init` and use a development build to get phone alerts; until then they appear in the in-app inbox.
- **Share intent (Fraud Shield):** sharing a message straight from WhatsApp needs `expo-share-intent` and a development build; deferred.
- **Screenshot OCR:** Tesseract isn't installed on this laptop (`winget install UB-Mannheim.TesseractOCR` + tessdata, see backend/ml_models/README.md).
- **Scam classifier:** disabled until a trained model or labelled dataset exists (`requirements-ml-classifier.txt` when needed).
- **End-to-end test scripts:** the puppeteer web tests used to verify steps 20–21 live outside the repo. They could be added under `mobile/e2e/`.
- **Docker/WSL memory:** under long, heavy load the WSL VM hoards memory and Docker freezes. The workaround is `wsl --shutdown`, restarting Docker Desktop, then `docker compose up -d`. A suggested permanent fix is a `%USERPROFILE%\.wslconfig` with `memory=8GB` and `autoMemoryReclaim=gradual` (not applied yet).

---

## How to run (Windows dev laptop)

1. **Local services.** Start Docker Desktop, then, from the repo root:
   ```powershell
   docker compose -f backend/docker-compose.dev.yml up -d
   ```
2. **API.** In a new terminal, from `backend/`. The API runs on http://localhost:8000 and the OTP codes print in this terminal as `dev_otp_code`.
   ```powershell
   .venv\Scripts\uvicorn app.main:app --reload
   ```
3. **Android emulator.** In a new terminal:
   ```powershell
   emulator -avd Pixel_8_API_35
   ```
4. **Mobile app.** In a new terminal, from `mobile/`, run the following, then press `a` to open the app in the emulator:
   ```powershell
   npx expo start
   ```

The emulator reaches the PC's API at `http://10.0.2.2:8000/api/v1`; this is already set in `mobile/.env`. A physical phone needs the PC's LAN IP instead.

**Emulator setup details:**
- Android SDK: `%LOCALAPPDATA%\Android\Sdk`
- JDK 17: `%LOCALAPPDATA%\Android\jdk17`
- User environment variables `ANDROID_HOME` and `JAVA_HOME` are set, and the SDK tools are on `PATH`.
- AVD `Pixel_8_API_35` (Android 15, 2 GB RAM). `hw.keyboard=yes` is set so the PC keyboard works in the emulator.

**Checks** (from `mobile/`):
```powershell
npm run typecheck
npm test
npm run check:i18n
```

---

## Working agreement
- Build strictly in spec order. Each step ends with its "Done when" check from the spec.
- Record every deviation from the spec in [ASSUMPTIONS.md](ASSUMPTIONS.md).
- Commit and push to `main` of the private repo `atharvakh7/Saathi_AI_FinPartner` only when asked.
