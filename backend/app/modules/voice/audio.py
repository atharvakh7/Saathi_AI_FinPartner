"""Audio conversion for STT (spec §5.11): any supported upload -> 16 kHz mono 16-bit WAV."""

import logging
import subprocess
import wave
from functools import lru_cache
from pathlib import Path

from app.ai.base import AIUnavailable, run_blocking
from app.core.config import settings

log = logging.getLogger(__name__)

MAX_AUDIO_SEC = 60


@lru_cache
def ffmpeg_cmd() -> str:
    if settings.FFMPEG_CMD:
        return settings.FFMPEG_CMD
    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise AIUnavailable("ffmpeg not found: set FFMPEG_CMD or install imageio-ffmpeg") from exc
    return imageio_ffmpeg.get_ffmpeg_exe()


def _convert_sync(src: str, dst: str) -> None:
    cmd = [
        ffmpeg_cmd(), "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-i", src,
        "-t", str(MAX_AUDIO_SEC + 1),  # never decode more than we accept
        "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", "-f", "wav", dst,
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    if result.returncode != 0:
        raise ValueError(f"could not decode audio: {result.stderr.decode(errors='replace')[:200]}")


async def convert_to_wav16k(src: str | Path, dst: str | Path) -> float:
    """Converts `src` into `dst` and returns the duration in seconds.

    Raises ValueError for undecodable audio and AIUnavailable when ffmpeg is missing.
    """
    await run_blocking("ffmpeg", 4, _convert_sync, str(src), str(dst))
    return wav_duration_sec(dst)


def wav_duration_sec(path: str | Path) -> float:
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())
