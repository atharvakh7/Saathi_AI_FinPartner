"""Text-to-speech with Piper (spec §3.2, A8).

`synthesize(text, language)` returns WAV bytes, or None when no voice is configured for the
language (the app then speaks with on-device TTS). Voices load lazily and are cached.
"""

import io
import logging
import threading
import wave
from pathlib import Path

from app.ai.base import AIUnavailable, run_blocking
from app.core.config import settings

log = logging.getLogger(__name__)

_voices: dict[str, object] = {}
_voices_lock = threading.Lock()


def voice_path(language: str) -> Path | None:
    value = {
        "en": settings.PIPER_VOICE_EN,
        "hi": settings.PIPER_VOICE_HI,
        "mr": settings.PIPER_VOICE_MR,
        "ta": settings.PIPER_VOICE_TA,
    }.get(language, "")
    path = settings.resolve_path(value)
    return path if path and path.is_file() and Path(f"{path}.json").is_file() else None


def _piper_installed() -> bool:
    try:
        import piper  # noqa: F401
    except ImportError:
        return False
    return True


def has_voice(language: str) -> bool:
    return voice_path(language) is not None and _piper_installed()


def is_available() -> bool:
    return any(has_voice(lang) for lang in ("en", "hi", "mr", "ta"))


def _voice(language: str):
    voice = _voices.get(language)
    if voice is None:
        with _voices_lock:
            voice = _voices.get(language)
            if voice is None:
                from piper import PiperVoice

                path = voice_path(language)
                log.info("loading piper voice", extra={"language": language, "voice": path.name})
                voice = _voices[language] = PiperVoice.load(path)
    return voice


def _synthesize_sync(text: str, language: str) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        _voice(language).synthesize_wav(text, wf)
    return buf.getvalue()


async def synthesize(text: str, language: str) -> bytes | None:
    """WAV bytes, or None when there is no voice for this language."""
    text = text.strip()
    if not text or not has_voice(language):
        return None
    try:
        return await run_blocking("tts", 2, _synthesize_sync, text, language)
    except Exception as exc:  # a broken voice file must not break the chat reply
        log.error("tts failed", extra={"language": language, "error": repr(exc)})
        raise AIUnavailable("text-to-speech failed") from exc
