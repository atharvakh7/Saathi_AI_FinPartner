"""Local-language scheme content (spec §5.6 "Local-language simplification").

The LLM (scheme_simplify.md) rewrites name, benefit summary, description, steps, documents and rule
explanations at about class-6 reading level. Stored in scheme_translations with generated_by='llm',
reviewed=false; admins can overwrite with generated_by='human' (step 18).

Checked before storing: same number of steps and documents, every rule key present, and every
number from the English text still present (amounts, ages, "7/12") — a translation that changes a
number is worse than none.

    .venv/Scripts/python -m app.modules.schemes.translate      # fill all missing (schemes.translate_missing)
"""

import asyncio
import json
import logging
import re
import sys
import unicodedata
import uuid

from pydantic import BaseModel, ValidationError
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import llm_client
from app.ai.base import AIOutputError, AIUnavailable
from app.ai.prompts import language_name, render
from app.core.db import SessionLocal
from app.core.enums import TRANSLATION_LANGUAGES
from app.core.redis import redis_client
from app.modules.schemes.models import Scheme, SchemeDocument, SchemeEligibilityRule, SchemeStep, SchemeTranslation

log = logging.getLogger(__name__)

ON_DEMAND_TIMEOUT_SEC = 120
BATCH_TIMEOUT_SEC = 240
ITEM_LOCK_TTL_SEC = 300


class _Step(BaseModel):
    title: str
    description: str


class _SchemeOut(BaseModel):
    name: str
    benefit_summary: str
    description: str
    steps: list[_Step]
    documents: list[str]
    rule_explanations: dict[str, str]


async def english_content(session: AsyncSession, scheme: Scheme) -> dict:
    """The translatable content in the stored JSON shape (spec §6.1 scheme_translations.content)."""
    steps = (
        await session.execute(select(SchemeStep).where(SchemeStep.scheme_id == scheme.id).order_by(SchemeStep.step_no))
    ).scalars()
    docs = (
        await session.execute(
            select(SchemeDocument)
            .where(SchemeDocument.scheme_id == scheme.id)
            .order_by(SchemeDocument.sort_order, SchemeDocument.document_name_en)
        )
    ).scalars()
    rules = (
        await session.execute(
            select(SchemeEligibilityRule)
            .where(SchemeEligibilityRule.scheme_id == scheme.id)
            .order_by(SchemeEligibilityRule.rule_key)
        )
    ).scalars()
    return {
        "name": scheme.name_en,
        "benefit_summary": scheme.benefit_summary_en,
        "description": scheme.description_en,
        "steps": [{"title": s.title_en, "description": s.description_en} for s in steps],
        "documents": [d.document_name_en for d in docs],
        "rule_explanations": {r.rule_key: r.explanation_en for r in rules},
    }


def _numbers(text: str) -> set[str]:
    """Digit groups with thousands separators removed: '₹1,50,000' -> {'150000'}.

    Devanagari/Tamil digits count as the same number ('७/१२' == '7/12').
    """
    text = "".join(str(unicodedata.digit(ch)) if ch.isdigit() else ch for ch in text)
    return set(re.findall(r"[0-9]+", re.sub(r"(?<=[0-9]),(?=[0-9])", "", text)))


def _all_text(content: dict) -> str:
    parts = [content["name"], content["benefit_summary"], content["description"], *content["documents"]]
    parts += [f"{s['title']} {s['description']}" for s in content["steps"]]
    parts += list(content["rule_explanations"].values())
    return "\n".join(parts)


# A translation must not mix in another Indian script (e.g. Hindi words inside Tamil text).
_FOREIGN_SCRIPT = {
    "hi": re.compile(r"[஀-௿]"),  # Tamil
    "mr": re.compile(r"[஀-௿]"),
    "ta": re.compile(r"[ऀ-ॿ]"),  # Devanagari
}


def check(source: dict, out: _SchemeOut, language: str) -> str | None:
    """Returns a problem description, or None when the translation is usable."""
    if len(out.steps) != len(source["steps"]):
        return f"steps {len(out.steps)} != {len(source['steps'])}"
    if len(out.documents) != len(source["documents"]):
        return f"documents {len(out.documents)} != {len(source['documents'])}"
    if set(out.rule_explanations) != set(source["rule_explanations"]):
        return "rule keys changed"
    untranslated = sum(a.strip() == b for a, b in zip(out.documents, source["documents"]))
    if untranslated * 2 > len(source["documents"]):
        return f"{untranslated} documents left in English"
    data = out.model_dump()
    texts = [data["name"], data["benefit_summary"], data["description"], *data["documents"],
             *(v for s in data["steps"] for v in s.values()), *data["rule_explanations"].values()]
    if any(not t.strip() for t in texts):
        return "empty text"
    foreign = _FOREIGN_SCRIPT.get(language)
    if foreign and any(foreign.search(t) for t in texts):
        return "mixed scripts"
    lost = _numbers(_all_text(source)) - _numbers(_all_text(data))
    if lost:
        return f"numbers lost: {sorted(lost)}"
    return None


async def _generate(source: dict, language: str, timeout: float) -> dict | None:
    prompt = render(
        "scheme_simplify", language_name=language_name(language),
        content_json=json.dumps(source, ensure_ascii=False, indent=1),
    )
    for attempt in range(2):  # one retry on unusable output
        try:
            result = await llm_client.chat_completion(
                [{"role": "user", "content": prompt}], json_schema=_SchemeOut, temperature=0.2, max_tokens=3000,
                timeout=timeout,
            )
            out = result.data
        except (AIOutputError, ValidationError) as exc:
            log.warning("scheme translation output unusable", extra={"attempt": attempt + 1, "error": repr(exc)})
            continue
        problem = check(source, out, language)
        if problem is None:
            data = out.model_dump()
            return {k: (v.strip() if isinstance(v, str) else v) for k, v in data.items()}
        log.warning("scheme translation rejected", extra={"attempt": attempt + 1, "problem": problem})
    return None


async def translate_scheme(
    session: AsyncSession, scheme: Scheme, language: str, timeout: float = ON_DEMAND_TIMEOUT_SEC
) -> SchemeTranslation | None:
    """Create the translation if missing. Returns the stored row, or None (caller falls back to English).

    Raises AIUnavailable when the LLM server is down. A per-item Redis lock keeps two requests from
    generating the same translation at once; the loser gets None and shows English this time.
    """
    existing = await _get(session, scheme.id, language)
    if existing is not None:
        return existing
    lock = f"schemes:translate:{scheme.id}:{language}"
    try:
        if not await redis_client.set(lock, "1", nx=True, ex=ITEM_LOCK_TTL_SEC):
            return None
    except RedisError:
        lock = None
    try:
        source = await english_content(session, scheme)
        content = await _generate(source, language, timeout)
        if content is None:
            log.warning("scheme translation skipped", extra={"slug": scheme.slug, "language": language})
            return None
        await session.execute(
            insert(SchemeTranslation)
            .values(scheme_id=scheme.id, language=language, content=content, generated_by="llm", reviewed=False)
            .on_conflict_do_nothing()  # an admin (or another worker) may have filled it meanwhile
        )
        await session.commit()
        return await _get(session, scheme.id, language)
    finally:
        if lock:
            try:
                await redis_client.delete(lock)
            except RedisError:
                pass


async def _get(session: AsyncSession, scheme_id: uuid.UUID, language: str) -> SchemeTranslation | None:
    return (
        await session.execute(
            select(SchemeTranslation).where(SchemeTranslation.scheme_id == scheme_id,
                                            SchemeTranslation.language == language)
        )
    ).scalar_one_or_none()


LOCK_KEY = "schemes:translate:lock"
LOCK_TTL_SEC = 3 * 3600


async def translate_missing(languages=TRANSLATION_LANGUAGES) -> int:
    """schemes.translate_missing (spec §5.10): fill every missing translation. Returns rows created."""
    try:
        if not await redis_client.set(LOCK_KEY, "1", nx=True, ex=LOCK_TTL_SEC):
            log.info("schemes translate_missing already running elsewhere; skipped")
            return 0
    except RedisError:
        pass
    created = 0
    try:
        async with SessionLocal() as session:
            schemes = list((await session.execute(
                select(Scheme).where(Scheme.is_active).order_by(Scheme.level, Scheme.slug)
            )).scalars())
            done = set((await session.execute(select(SchemeTranslation.scheme_id, SchemeTranslation.language))).all())
            for language in languages:
                for scheme in schemes:
                    if (scheme.id, language) in done:
                        continue
                    if await translate_scheme(session, scheme, language, timeout=BATCH_TIMEOUT_SEC) is not None:
                        created += 1
    except AIUnavailable as exc:
        log.warning("scheme translation paused: LLM unavailable", extra={"error": str(exc)})
    finally:
        try:
            await redis_client.delete(LOCK_KEY)
        except RedisError:
            pass
    log.info("schemes translate_missing finished", extra={"rows_created": created})
    return created


if __name__ == "__main__":
    from app.core.logging import configure_logging

    configure_logging()
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    print(asyncio.run(translate_missing()))
