"""OpenAI-compatible chat completions (Ollama by default; any hosted endpoint via env, spec A7).

`chat_completion(messages, json_schema=Model)` asks for structured output and validates it
with Pydantic (spec §8.2): the caller gets a validated object or `AIOutputError`, never
half-parsed JSON.
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.ai.base import AIOutputError, AIUnavailable, limiter
from app.core.config import settings

log = logging.getLogger(__name__)

_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)
_AVAILABILITY_TTL_SEC = 30
_availability: tuple[float, bool] | None = None


@dataclass
class LLMResult:
    text: str
    data: Any | None  # validated Pydantic object when json_schema was given
    tokens_in: int | None
    tokens_out: int | None


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.LLM_API_KEY}"} if settings.LLM_API_KEY else {}


def _url(path: str) -> str:
    return f"{settings.LLM_BASE_URL.rstrip('/')}/{path.lstrip('/')}"


def parse_json(text: str) -> Any:
    """Parse model output as JSON, tolerating ``` fences and leading/trailing prose."""
    cleaned = _FENCE.sub("", text.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


RETRY_STATUS = {429, 500, 502, 503, 504}  # overloaded / rate-limited: worth a pause and another try
RETRY_PAUSE_SEC = 1.5


async def _post_model(body: dict, timeout: float) -> dict:
    """One model: a second try after a short pause on transport errors, 429 and 5xx."""
    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(_url("chat/completions"), json=body, headers=_headers())
            resp.raise_for_status()
            return resp.json()
        except (httpx.TransportError, httpx.HTTPStatusError) as exc:
            last_exc = exc
            status = getattr(getattr(exc, "response", None), "status_code", None)
            log.warning("llm request failed", extra={"model": body.get("model"), "attempt": attempt + 1, "error": repr(exc)})
            if status is not None and status not in RETRY_STATUS:
                break  # other 4xx: retrying the same request won't help
            if attempt == 0:
                await asyncio.sleep(RETRY_PAUSE_SEC)
    raise AIUnavailable(f"LLM request failed: {last_exc!r}") from last_exc


async def _post(body: dict, timeout: float) -> tuple[dict, str]:
    """Try LLM_MODEL, then each LLM_FALLBACK_MODELS entry; returns (response, model used)."""
    last: AIUnavailable | None = None
    for model in settings.llm_models:
        try:
            return await _post_model({**body, "model": model}, timeout), model
        except AIUnavailable as exc:
            last = exc
    assert last is not None
    raise last


async def chat_completion(
    messages: list[dict[str, str]],
    json_schema: type[BaseModel] | None = None,
    temperature: float = 0.3,
    max_tokens: int = 500,
    timeout: float | None = None,
) -> LLMResult:
    """Raises AIUnavailable (server down/misconfigured) or AIOutputError (unusable JSON)."""
    body: dict[str, Any] = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if settings.LLM_REASONING_EFFORT:
        body["reasoning_effort"] = settings.LLM_REASONING_EFFORT
    if json_schema is not None:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": json_schema.__name__, "schema": json_schema.model_json_schema(), "strict": True},
        }

    started = time.perf_counter()
    async with limiter("llm", settings.LLM_MAX_CONCURRENCY):
        try:
            payload, model_used = await _post(body, timeout or settings.LLM_TIMEOUT_SEC)
        except AIUnavailable:
            if json_schema is None:
                raise
            # Some OpenAI-compatible servers only support plain JSON mode.
            body["response_format"] = {"type": "json_object"}
            payload, model_used = await _post(body, timeout or settings.LLM_TIMEOUT_SEC)

    try:
        text = payload["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise AIOutputError("LLM response has no message content") from exc
    usage = payload.get("usage") or {}
    log.info(
        "llm completion",
        extra={
            "model": model_used,
            "ms": round((time.perf_counter() - started) * 1000),
            "tokens_in": usage.get("prompt_tokens"),
            "tokens_out": usage.get("completion_tokens"),
        },
    )

    data = None
    if json_schema is not None:
        try:
            data = json_schema.model_validate(parse_json(text))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise AIOutputError(f"LLM output failed {json_schema.__name__} validation", raw_text=text) from exc
    return LLMResult(text=text, data=data, tokens_in=usage.get("prompt_tokens"), tokens_out=usage.get("completion_tokens"))


async def is_available() -> bool:
    """The endpoint answers and serves LLM_MODEL (cached for 30 s)."""
    global _availability
    now = time.monotonic()
    if _availability and now - _availability[0] < _AVAILABILITY_TTL_SEC:
        return _availability[1]
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(_url("models"), headers=_headers())
        resp.raise_for_status()
        ids = {m.get("id") for m in resp.json().get("data", [])}
        ok = any(m in ids or f"models/{m}" in ids for m in settings.llm_models)  # Gemini lists "models/<id>"
    except Exception:
        ok = False
    _availability = (now, ok)
    return ok
