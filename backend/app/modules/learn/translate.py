"""Fill missing glossary and lesson translations with the LLM (spec §5.8).

Rows are stored with generated_by='llm', reviewed=false; admins can overwrite them with
generated_by='human' (step 18). Existing rows are never touched, so re-running is safe.

    .venv/Scripts/python -m app.modules.learn.translate            # all missing
    .venv/Scripts/python -m app.modules.learn.translate glossary   # only glossary

Step 17 runs this as the `glossary.translate_missing` job; the API also starts it in the
background at startup (TRANSLATE_ON_STARTUP).
"""

import argparse
import asyncio
import logging
import sys

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
from app.modules.learn import term_detector
from app.modules.learn.models import GlossaryTerm, GlossaryTranslation, Lesson, LessonTranslation

log = logging.getLogger(__name__)


class _TermOut(BaseModel):
    term_local: str
    definition: str
    example: str
    analogy: str
    key_takeaway: str


class _LessonOut(BaseModel):
    title: str
    body_md: str


# Column limits (spec §6.1); a translation that doesn't fit is skipped, not truncated mid-sentence.
_TERM_LIMITS = {"term_local": 120, "definition": 600, "example": 600, "analogy": 500, "key_takeaway": 250}
_LESSON_LIMITS = {"title": 200}


def _fits(data: BaseModel, limits: dict[str, int]) -> bool:
    return all(0 < len(getattr(data, k).strip()) <= n for k, n in limits.items())


async def _ask(prompt: str, schema: type[BaseModel], max_tokens: int):
    for attempt in range(2):  # one retry on unusable output
        try:
            result = await llm_client.chat_completion(
                [{"role": "user", "content": prompt}], json_schema=schema, temperature=0.2, max_tokens=max_tokens,
                timeout=180,
            )
            return result.data
        except (AIOutputError, ValidationError) as exc:
            log.warning("translation output unusable", extra={"attempt": attempt + 1, "error": repr(exc)})
    return None


async def translate_glossary(session: AsyncSession, languages=TRANSLATION_LANGUAGES) -> int:
    terms = list((await session.execute(select(GlossaryTerm).where(GlossaryTerm.is_active))).scalars())
    done = set((await session.execute(select(GlossaryTranslation.term_id, GlossaryTranslation.language))).all())
    created = 0
    for lang in languages:
        for term in terms:
            if (term.id, lang) in done:
                continue
            prompt = render(
                "glossary_translate", language_name=language_name(lang), term_en=term.term_en,
                definition_en=term.definition_en, example_en=term.example_en, analogy_en=term.analogy_en,
                key_takeaway_en=term.key_takeaway_en,
            )
            data = await _ask(prompt, _TermOut, 700)
            if data is None or not _fits(data, _TERM_LIMITS):
                log.warning("glossary translation skipped", extra={"slug": term.slug, "language": lang})
                continue
            await session.execute(insert(GlossaryTranslation).values(
                term_id=term.id, language=lang, generated_by="llm", reviewed=False,
                **{k: getattr(data, k).strip() for k in _TERM_LIMITS},
            ).on_conflict_do_nothing())  # another run (or an admin) may have filled it meanwhile
            await session.commit()
            created += 1
    if created:
        await term_detector.invalidate()
    return created


async def translate_lessons(session: AsyncSession, languages=TRANSLATION_LANGUAGES) -> int:
    lessons = list((await session.execute(select(Lesson).where(Lesson.is_active).order_by(Lesson.sort_order))).scalars())
    done = set((await session.execute(select(LessonTranslation.lesson_id, LessonTranslation.language))).all())
    created = 0
    for lang in languages:
        for lesson in lessons:
            if (lesson.id, lang) in done:
                continue
            prompt = render("lesson_translate", language_name=language_name(lang), title_en=lesson.title_en,
                            body_md_en=lesson.body_md_en)
            data = await _ask(prompt, _LessonOut, 2500)
            if data is None or not _fits(data, _LESSON_LIMITS) or len(data.body_md) < 0.4 * len(lesson.body_md_en):
                log.warning("lesson translation skipped", extra={"slug": lesson.slug, "language": lang})
                continue
            await session.execute(insert(LessonTranslation).values(
                lesson_id=lesson.id, language=lang, title=data.title.strip(), body_md=data.body_md.strip(),
                generated_by="llm", reviewed=False,
            ).on_conflict_do_nothing())
            await session.commit()
            created += 1
    return created


LOCK_KEY = "learn:translate:lock"
LOCK_TTL_SEC = 3 * 3600


async def translate_missing(kinds=("glossary", "lessons")) -> dict[str, int]:
    """Returns how many rows were created per kind. Stops quietly if the LLM is unavailable.

    A Redis lock keeps two runs (e.g. API startup and the CLI) from translating the same items.
    """
    try:
        if not await redis_client.set(LOCK_KEY, "1", nx=True, ex=LOCK_TTL_SEC):
            log.info("translate_missing already running elsewhere; skipped")
            return {}
    except RedisError:
        pass  # no lock available: the ON CONFLICT inserts still keep the data correct
    out = {}
    try:
        out = await _translate(kinds)
    finally:
        try:
            await redis_client.delete(LOCK_KEY)
        except RedisError:
            pass
    return out


async def _translate(kinds) -> dict[str, int]:
    out = {}
    async with SessionLocal() as session:
        try:
            if "glossary" in kinds:
                out["glossary"] = await translate_glossary(session)
            if "lessons" in kinds:
                out["lessons"] = await translate_lessons(session)
        except AIUnavailable as exc:
            log.warning("translation paused: LLM unavailable", extra={"error": str(exc)})
    log.info("translate_missing finished", extra={"rows_created": out})
    return out


if __name__ == "__main__":
    from app.core.logging import configure_logging

    configure_logging()
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("kinds", nargs="*", choices=["glossary", "lessons", []], default=[])
    args = parser.parse_args()
    print(asyncio.run(translate_missing(tuple(args.kinds) or ("glossary", "lessons"))))
