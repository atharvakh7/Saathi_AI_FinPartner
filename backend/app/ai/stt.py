"""Speech-to-text with whisper.cpp (spec §3.2, §7.4 /chat/voice).

Two backends, same behaviour:
- WHISPER_SERVER_URL set: a whisper.cpp `whisper-server` (GPU container `whisper` in
  docker-compose.dev.yml). Fast enough for the large-v3-turbo model.
- WHISPER_SERVER_URL blank: in-process pywhispercpp on CPU with WHISPER_MODEL_PATH.

Input is a 16 kHz mono WAV (app.modules.voice.audio converts uploads). Language is detected
automatically but restricted to en/hi/mr/ta; if Whisper picks another language, the hint
(the user's preferred language) is used instead.
"""

import logging
import math
import re
import threading
import time
import wave
from dataclasses import dataclass
from pathlib import Path

import httpx
import numpy as np

from app.ai.base import AIUnavailable, limiter, run_blocking
from app.core.config import settings
from app.core.enums import LANGUAGES

log = logging.getLogger(__name__)

SAMPLE_RATE = 16_000
_WHISPER_NAMES = {"english": "en", "hindi": "hi", "marathi": "mr", "tamil": "ta"}
_model = None
_model_lock = threading.Lock()
_server_status: tuple[float, bool] | None = None


@dataclass(frozen=True)
class Transcription:
    text: str
    language: str
    confidence: float  # 0..1


# --- shared --------------------------------------------------------------------------

def _code(lang: str | None) -> str | None:
    if not lang:
        return None
    lang = lang.lower()
    return _WHISPER_NAMES.get(lang, lang)


def pick_language(detected: str | None, probability: float, probs: dict[str, float], hint: str | None) -> tuple[str, float]:
    """Restrict Whisper's language guess to en/hi/mr/ta and apply the hi/mr tie-break."""
    detected = _code(detected)
    candidates = {_code(k): float(v) for k, v in probs.items() if _code(k) in LANGUAGES}
    if detected in LANGUAGES:
        language, conf = detected, probability
    elif candidates and max(candidates.values()) >= 0.1:
        language = max(candidates, key=candidates.get)
        conf = candidates[language]
    elif hint in LANGUAGES:
        # Whisper guessed a language we don't support (small/CPU sometimes labels Marathi as
        # Bengali or Sinhala). The user's own language is the best guess; never fall back to
        # English, which makes Whisper translate instead of transcribe.
        language, conf = hint, 0.0
    else:
        language = max(candidates, key=candidates.get) if candidates else "en"
        conf = 0.0
    # Whisper often labels Marathi speech as Hindi. As with Devanagari text (spec §5.3 step 2),
    # the user's own hi/mr choice breaks the tie between the two.
    if language in ("hi", "mr") and hint in ("hi", "mr"):
        language = hint
    return language, conf


def read_wav_16k(path: str | Path) -> np.ndarray:
    with wave.open(str(path), "rb") as wf:
        if wf.getframerate() != SAMPLE_RATE or wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            raise ValueError("expected 16 kHz mono 16-bit WAV")
        frames = wf.readframes(wf.getnframes())
    return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0


def _too_short(path: str | Path) -> bool:
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() < SAMPLE_RATE // 4  # < 0.25 s


def _server_url() -> str:
    return settings.WHISPER_SERVER_URL.rstrip("/")


def model_path() -> Path | None:
    path = settings.resolve_path(settings.WHISPER_MODEL_PATH)
    return path if path and path.is_file() else None


def is_available() -> bool:
    """Configured (server URL set, or local model + pywhispercpp present)."""
    if _server_url():
        return True
    if model_path() is None:
        return False
    try:
        import pywhispercpp  # noqa: F401
    except ImportError:
        return False
    return True


async def check_available() -> bool:
    """Like is_available(), but also pings the server (cached 30 s). Used by /health."""
    global _server_status
    if not _server_url():
        return is_available()
    now = time.monotonic()
    if _server_status and now - _server_status[0] < 30:
        return _server_status[1]
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            ok = (await client.get(f"{_server_url()}/")).status_code < 500
    except httpx.HTTPError:
        ok = False
    _server_status = (now, ok)
    return ok


# --- server backend (GPU) ------------------------------------------------------------

async def _server_call(client: httpx.AsyncClient, wav: bytes, language: str) -> dict:
    resp = await client.post(
        f"{_server_url()}/inference",
        files={"file": ("audio.wav", wav, "audio/wav")},
        data={"language": language, "response_format": "verbose_json", "temperature": "0.0"},
    )
    resp.raise_for_status()
    return resp.json()


# Whisper's non-speech annotations: "[BLANK_AUDIO]", "[Music]", "(applause)", "♪".
_NON_SPEECH = re.compile(
    r"\[[^\]]{1,40}\]|\((?:music|applause|laugh\w*|silence|inaudible|noise|blank_audio)[^)]{0,30}\)|[♪♫]",
    re.IGNORECASE,
)


def clean_text(text: str) -> str:
    return " ".join(_NON_SPEECH.sub(" ", text).split())


def decode_language(language: str) -> str:
    """Language passed to the decoder. Whisper small's Marathi decoder often fails outright on real
    speech (FLEURS: 73% CER, 4 of 8 clips unusable); its Hindi decoder writes the same Devanagari
    speech far better (42% CER) and 5x faster. The result is still labelled Marathi."""
    if language == "mr" and settings.WHISPER_MR_DECODE_AS in LANGUAGES:
        return settings.WHISPER_MR_DECODE_AS
    return language


def _segment_confidence(segments: list[dict]) -> float | None:
    probs = [math.exp(s["avg_logprob"]) for s in segments if isinstance(s.get("avg_logprob"), (int, float))]
    return float(np.mean(probs)) if probs else None


async def _transcribe_server(wav_path: str, hint: str | None) -> Transcription:
    wav = Path(wav_path).read_bytes()
    try:
        async with limiter("stt", 2), httpx.AsyncClient(timeout=120) as client:
            result = await _server_call(client, wav, "auto")
            detected = result.get("detected_language") or result.get("language")
            language, lang_conf = pick_language(
                detected,
                float(result.get("detected_language_probability") or 0.0),
                result.get("language_probabilities") or {},
                hint,
            )
            if _code(detected) != decode_language(language):  # decoded in another language: redo
                result = await _server_call(client, wav, decode_language(language))
    except httpx.HTTPError as exc:
        raise AIUnavailable(f"whisper server request failed: {exc!r}") from exc
    text = clean_text(result.get("text") or "")
    confidence = _segment_confidence(result.get("segments") or [])
    return Transcription(text=text, language=language, confidence=round(confidence if confidence is not None else lang_conf, 3))


# --- in-process backend (CPU) --------------------------------------------------------

def _load_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                path = model_path()
                if path is None:
                    raise AIUnavailable("WHISPER_MODEL_PATH is not set or the file is missing")
                try:
                    from pywhispercpp.model import Model
                except ImportError as exc:
                    raise AIUnavailable("pywhispercpp is not installed") from exc
                log.info("loading whisper model", extra={"path": path.name})
                _model = Model(
                    str(path),
                    n_threads=settings.WHISPER_THREADS,
                    print_realtime=False,
                    print_progress=False,
                    print_timestamps=False,
                    redirect_whispercpp_logs_to=None,
                )
    return _model


def _transcribe_local(wav_path: str, hint: str | None) -> Transcription:
    model = _load_model()
    audio = read_wav_16k(wav_path)
    (detected, lang_prob), probs = model.auto_detect_language(audio)
    language, lang_conf = pick_language(detected, float(lang_prob), probs, hint)
    segments = model.transcribe(audio, language=decode_language(language), extract_probability=True)
    text = clean_text(" ".join(s.text for s in segments))
    probs_seg = [s.probability for s in segments if s.probability is not None and not math.isnan(s.probability)]
    confidence = float(np.mean(probs_seg)) if probs_seg else lang_conf
    return Transcription(text=text, language=language, confidence=round(confidence, 3))


# --- public ----------------------------------------------------------------------------

async def transcribe(wav_path: str | Path, language_hint: str | None = None) -> Transcription:
    """Raises AIUnavailable if speech-to-text is not configured/reachable. Empty text = nothing heard."""
    if not is_available():
        raise AIUnavailable("speech-to-text is not configured")
    if _too_short(wav_path):
        return Transcription("", language_hint or "en", 0.0)
    if _server_url():
        return await _transcribe_server(str(wav_path), language_hint)
    return await run_blocking("stt", 1, _transcribe_local, str(wav_path), language_hint)


def warm_up_sync() -> None:
    """Load the local model (no-op in server mode; the server loads its model at start)."""
    if not _server_url():
        _load_model()
