"""Speech in, speech out (spec §5.11, §7.4 /chat/transcribe, /chat/tts).

Uploads: ≤ 5 MB, ≤ 60 s, audio/m4a|mp4|mpeg|wav|webm (plus the aliases phones actually send).
The recording lives only in a temp directory that is deleted in `finally` (never stored).

TTS audio is cached in the `saathi-tts-cache` bucket under `tts/{sha256(lang + text)}.wav` and
served by a presigned URL valid 10 minutes. Old objects are purged after 30 days (step 17).
"""

import asyncio
import hashlib
import logging
import shutil
import tempfile
from pathlib import Path

from botocore.exceptions import BotoCoreError, ClientError

from app.ai import stt, tts
from app.ai.base import AIUnavailable
from app.ai.stt import Transcription
from app.core.config import settings
from app.core.errors import AppError
from app.core.storage import TTS_URL_TTL_SEC, presigned_get, s3_client
from app.modules.voice.audio import MAX_AUDIO_SEC, convert_to_wav16k

log = logging.getLogger(__name__)

AUDIO_MAX_BYTES = 5 * 1024 * 1024
MIN_CONFIDENCE = 0.3
# Spec list first; then the names Android/iOS/browsers really use for the same formats.
AUDIO_TYPES = {
    "audio/m4a", "audio/mp4", "audio/mpeg", "audio/wav", "audio/webm",
    "audio/x-m4a", "audio/aac", "audio/mp3", "audio/x-wav", "audio/wave", "audio/vnd.wave", "video/webm",
}
_SUFFIX = {"audio/mpeg": ".mp3", "audio/mp3": ".mp3", "audio/webm": ".webm", "video/webm": ".webm"}


# --- Speech to text ----------------------------------------------------------------

async def transcribe_upload(data: bytes, content_type: str | None, language_hint: str | None) -> Transcription:
    """Validate, convert, transcribe. Raises AppError with the codes from spec §7.4."""
    if len(data) > AUDIO_MAX_BYTES:
        raise AppError("PAYLOAD_TOO_LARGE")
    mime = (content_type or "").split(";")[0].strip().lower()
    if mime not in AUDIO_TYPES:
        raise AppError("UNSUPPORTED_MEDIA_TYPE")

    workdir = Path(tempfile.mkdtemp(prefix="saathi-voice-"))
    try:
        src = workdir / f"in{_SUFFIX.get(mime, '.bin')}"
        src.write_bytes(data)
        del data
        wav = workdir / "in.wav"
        try:
            duration = await convert_to_wav16k(src, wav)
        except ValueError as exc:
            raise AppError("UNSUPPORTED_MEDIA_TYPE") from exc
        except AIUnavailable as exc:
            raise AppError("UPSTREAM_AI_UNAVAILABLE") from exc
        if duration > MAX_AUDIO_SEC + 0.5:  # small slack for container padding
            raise AppError("PAYLOAD_TOO_LARGE", "Recordings can be up to 60 seconds.")
        try:
            result = await stt.transcribe(wav, language_hint)
        except AIUnavailable as exc:
            raise AppError("UPSTREAM_AI_UNAVAILABLE") from exc
    finally:
        shutil.rmtree(workdir, ignore_errors=True)  # never keep recordings (spec §8.2)

    if not result.text.strip() or result.confidence < MIN_CONFIDENCE:
        log.info("transcription rejected", extra={"chars": len(result.text), "confidence": result.confidence})
        raise AppError("TRANSCRIPTION_FAILED")
    log.info("transcribed", extra={"language": result.language, "confidence": result.confidence,
                                   "seconds": round(duration, 1)})
    return result


# --- Text to speech ----------------------------------------------------------------

def cache_key(text: str, language: str) -> str:
    return f"tts/{hashlib.sha256((language + text).encode('utf-8')).hexdigest()}.wav"


def _exists_sync(key: str) -> bool:
    try:
        s3_client().head_object(Bucket=settings.S3_BUCKET_TTS, Key=key)
        return True
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
            return False
        raise


def _put_sync(key: str, wav: bytes) -> None:
    s3_client().put_object(Bucket=settings.S3_BUCKET_TTS, Key=key, Body=wav, ContentType="audio/wav")


async def speech_url(text: str, language: str) -> str | None:
    """Presigned URL of the spoken text, or None when there is no voice for the language (A8).

    Raises AIUnavailable when synthesis or storage fails (callers decide: chat sends audio=null,
    /chat/tts returns 503).
    """
    text = " ".join(text.split())
    if not text or not tts.has_voice(language):
        return None
    key = cache_key(text, language)
    try:
        cached = await asyncio.to_thread(_exists_sync, key)
    except (BotoCoreError, ClientError) as exc:
        raise AIUnavailable(f"tts cache unavailable: {exc}") from exc
    if not cached:
        wav = await tts.synthesize(text, language)
        if wav is None:
            return None
        try:
            await asyncio.to_thread(_put_sync, key, wav)
        except (BotoCoreError, ClientError) as exc:
            raise AIUnavailable(f"tts cache unavailable: {exc}") from exc
    return presigned_get(settings.S3_BUCKET_TTS, key, TTS_URL_TTL_SEC)
