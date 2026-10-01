"""Download 8 FLEURS dev clips each for hi/mr/ta (+ transcripts) for bench_whisper.

Streams the archives and stops after 8 clips, so only a few MB are downloaded per language.
Clips are converted to 16 kHz mono 16-bit WAV with the app's own ffmpeg path.

Run from backend/:  .venv/Scripts/python -m scripts.benchmarks.fetch_fleurs
"""

import asyncio
import os
import tarfile
from pathlib import Path

import httpx

from app.modules.voice.audio import convert_to_wav16k

OUT = Path(__file__).parent / "data" / "fleurs"
BASE = "https://huggingface.co/datasets/google/fleurs/resolve/main/data"
CLIPS = 8


class _Stream:
    """Minimal file-like wrapper over an httpx byte stream for tarfile's stream mode."""

    def __init__(self, iterator):
        self._it, self._buf = iterator, b""

    def read(self, n=-1):
        while n < 0 or len(self._buf) < n:
            try:
                self._buf += next(self._it)
            except StopIteration:
                break
        data, self._buf = (self._buf, b"") if n < 0 else (self._buf[:n], self._buf[n:])
        return data


def fetch(lang: str) -> None:
    out = OUT / lang
    out.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=True, timeout=120) as client:
        (out / "dev.tsv").write_bytes(client.get(f"{BASE}/{lang}/dev.tsv").content)
        with client.stream("GET", f"{BASE}/{lang}/audio/dev.tar.gz") as resp:
            resp.raise_for_status()
            n = 0
            with tarfile.open(fileobj=_Stream(resp.iter_bytes()), mode="r|gz") as tf:
                for member in tf:
                    if member.isfile() and member.name.endswith(".wav"):
                        (out / os.path.basename(member.name)).write_bytes(tf.extractfile(member).read())
                        n += 1
                        if n >= CLIPS:
                            break
    print(f"{lang}: {n} clips")


async def convert_all() -> None:
    for wav in OUT.glob("*/*.wav"):
        tmp = wav.with_suffix(".tmp.wav")
        await convert_to_wav16k(wav, tmp)
        os.replace(tmp, wav)


if __name__ == "__main__":
    for lang in ("hi_in", "mr_in", "ta_in"):
        fetch(lang)
    asyncio.run(convert_all())
    print(f"saved to {OUT}")
