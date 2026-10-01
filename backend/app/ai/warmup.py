"""Preload AI models in the background at API startup (spec §5.1: lifespan loads models).

The first LLM call after Ollama starts takes ~1 minute to load weights; doing it here means
the first user doesn't hit a timeout. Each step is independent and failures only log.
"""

import asyncio
import logging
import time

from app.ai import embeddings, lang_detect, llm_client, stt, tts

log = logging.getLogger(__name__)

LLM_WARMUP_TIMEOUT_SEC = 300


async def _step(name: str, coro) -> None:
    started = time.perf_counter()
    try:
        await coro
        log.info("ai warm-up done", extra={"model": name, "sec": round(time.perf_counter() - started, 1)})
    except Exception as exc:
        log.warning("ai warm-up skipped", extra={"model": name, "error": repr(exc)})


async def warm_up() -> None:
    await asyncio.gather(
        _step("llm", llm_client.chat_completion(
            [{"role": "user", "content": "Hi"}], max_tokens=1, timeout=LLM_WARMUP_TIMEOUT_SEC
        )),
        _step("embeddings", embeddings.embed(["warm up"])),
        _step("lang_detect", asyncio.to_thread(lang_detect.detect_text_language, "नमस्ते")),
    )
    # Local CPU models load one after another to avoid a memory spike.
    if stt.is_available():
        await _step("whisper", asyncio.to_thread(stt.warm_up_sync))
    for lang in ("en", "hi", "mr", "ta"):
        if tts.has_voice(lang):
            await _step(f"piper:{lang}", asyncio.to_thread(tts._voice, lang))
