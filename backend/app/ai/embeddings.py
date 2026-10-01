"""Text embeddings via an OpenAI-compatible /embeddings endpoint (bge-m3 on Ollama, 1024-d)."""

import logging

import httpx

from app.ai.base import AIUnavailable, limiter
from app.core.config import settings

log = logging.getLogger(__name__)

BATCH_SIZE = 32


async def embed(texts: list[str]) -> list[list[float]]:
    """Returns one vector per input, in order. Raises AIUnavailable on any failure."""
    if not texts:
        return []
    headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"} if settings.LLM_API_KEY else {}
    url = f"{settings.EMBED_BASE_URL.rstrip('/')}/embeddings"
    vectors: list[list[float]] = []
    async with limiter("embed", settings.LLM_MAX_CONCURRENCY):
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SEC) as client:
            for i in range(0, len(texts), BATCH_SIZE):
                batch = texts[i : i + BATCH_SIZE]
                try:
                    resp = await client.post(url, json={"model": settings.EMBED_MODEL, "input": batch}, headers=headers)
                    resp.raise_for_status()
                    data = sorted(resp.json()["data"], key=lambda d: d["index"])
                except (httpx.HTTPError, KeyError, ValueError) as exc:
                    raise AIUnavailable(f"embedding request failed: {exc!r}") from exc
                vectors.extend(d["embedding"] for d in data)
    if len(vectors) != len(texts) or any(len(v) != settings.EMBED_DIM for v in vectors):
        raise AIUnavailable(f"embedding model must return {len(texts)} vectors of {settings.EMBED_DIM} dims")
    return vectors


async def embed_one(text: str) -> list[float]:
    return (await embed([text]))[0]
