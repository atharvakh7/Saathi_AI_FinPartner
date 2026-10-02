"""Settings loaded from environment / backend/.env (spec §9.1)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_ENV: Literal["local", "production"] = "local"
    API_BASE_URL: str = "http://localhost:8000"
    API_PREFIX: str = "/api/v1"
    TIMEZONE: str = "Asia/Kolkata"
    CORS_ORIGINS: str = ""
    GRIEVANCE_EMAIL: str = "grievance@example.com"
    ADMIN_PHONE_E164: str = ""

    # Data stores
    DATABASE_URL: str = "postgresql+asyncpg://saathi:saathi@localhost:5432/saathi"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth / crypto — required, >= 32 chars (spec §8.3)
    JWT_SECRET: str
    DATA_ENCRYPTION_KEY: str
    OTP_HMAC_KEY: str
    JWT_ACCESS_TTL_SEC: int = 900
    JWT_REFRESH_TTL_DAYS: int = 30
    OTP_PROVIDER: Literal["console", "msg91"] = "console"
    MSG91_AUTH_KEY: str = ""
    MSG91_TEMPLATE_ID: str = ""
    MSG91_SENDER_ID: str = ""

    # Rate limits
    RATE_LIMIT_USER_PER_MIN: int = 120
    RATE_LIMIT_IP_PER_MIN: int = 300

    # LLM / embeddings
    LLM_BASE_URL: str = "http://ollama:11434/v1"
    LLM_MODEL: str = "gemma4:e4b-it-qat"
    # Comma-separated models tried in order when LLM_MODEL is overloaded (503/429) or fails; blank = none.
    LLM_FALLBACK_MODELS: str = ""
    LLM_API_KEY: str = "ollama"
    LLM_TIMEOUT_SEC: int = 60
    LLM_MAX_CONCURRENCY: int = 2
    # Sent as `reasoning_effort` so "thinking" models answer directly (fast, schema-safe). Blank = omit.
    LLM_REASONING_EFFORT: str = "none"
    EMBED_BASE_URL: str = "http://ollama:11434/v1"
    EMBED_MODEL: str = "bge-m3"
    EMBED_DIM: int = 1024

    # Speech / OCR / classifier
    # whisper.cpp server (GPU container). Blank = run WHISPER_MODEL_PATH in-process on CPU.
    WHISPER_SERVER_URL: str = ""
    WHISPER_MODEL_PATH: str = ""
    WHISPER_THREADS: int = 4
    # Decode Marathi speech with this language's decoder ('mr' = native). See stt.decode_language.
    WHISPER_MR_DECODE_AS: str = "hi"
    PIPER_VOICE_EN: str = ""
    PIPER_VOICE_HI: str = ""
    PIPER_VOICE_MR: str = ""
    PIPER_VOICE_TA: str = ""
    TESSERACT_CMD: str = "tesseract"
    TESSDATA_PREFIX: str = ""
    SCAM_MODEL_DIR: str = ""
    # Preload AI models in the background when the API starts.
    AI_WARMUP: bool = True
    # Fill missing glossary/lesson translations with the LLM after warm-up (spec §5.8).
    TRANSLATE_ON_STARTUP: bool = True
    # Blank = use the ffmpeg binary bundled with the imageio-ffmpeg package.
    FFMPEG_CMD: str = ""

    # Object storage
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_MEDIA: str = "saathi-media"
    S3_BUCKET_TTS: str = "saathi-tts-cache"
    S3_REGION: str = "ap-south-1"

    # Push
    EXPO_PUSH_URL: str = "https://exp.host/--/api/v2/push/send"
    EXPO_ACCESS_TOKEN: str = ""

    # Background jobs (spec §5.9–5.10). Off: work runs inside the API process and the beat schedule
    # doesn't run (fine for a single dev machine). On: the API queues Celery tasks; run a worker + beat.
    CELERY_ENABLED: bool = False
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    INSIGHTS_DEBOUNCE_SEC: int = 60
    PUSH_MAX_PER_DAY: int = 3

    # Request body limits (spec §8.3)
    MAX_JSON_BODY_BYTES: int = 64 * 1024
    MAX_UPLOAD_BODY_BYTES: int = 6 * 1024 * 1024

    @field_validator("JWT_SECRET", "DATA_ENCRYPTION_KEY", "OTP_HMAC_KEY")
    @classmethod
    def _strip_secret(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 32:
            raise ValueError("must be at least 32 characters")
        return v

    @model_validator(mode="after")
    def _production_guards(self) -> "Settings":
        if self.is_production:
            if self.OTP_PROVIDER == "console":
                raise ValueError("OTP_PROVIDER=console logs login codes and is not allowed in production")
            if not (self.MSG91_AUTH_KEY and self.MSG91_TEMPLATE_ID):
                raise ValueError("MSG91_AUTH_KEY and MSG91_TEMPLATE_ID are required in production")
        return self

    @property
    def llm_models(self) -> list[str]:
        """LLM_MODEL first, then the fallbacks (duplicates removed)."""
        models = [self.LLM_MODEL, *(m.strip() for m in self.LLM_FALLBACK_MODELS.split(","))]
        return list(dict.fromkeys(m for m in models if m))

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    def resolve_path(self, value: str) -> Path | None:
        """Resolve a model/voice path relative to backend/; None when blank."""
        if not value:
            return None
        p = Path(value)
        return p if p.is_absolute() else (BACKEND_DIR / p).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # required secrets come from env


settings = get_settings()
