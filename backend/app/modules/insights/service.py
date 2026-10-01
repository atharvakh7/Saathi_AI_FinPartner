"""Insight generation and the /insights feed (spec §5.9, §7.4).

New insights are written in the user's language: the LLM (insight_phrase.md) rewrites the English
template and is rejected if any number changes; then the English text is stored. Existing dedupe
keys are skipped before any LLM call.
"""

import logging
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from sqlalchemy import or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import llm_client
from app.ai.base import AIOutputError, AIUnavailable
from app.ai.prompts import language_name, render
from app.core.errors import AppError
from app.core.pagination import after_cursor, decode_cursor, encode_cursor
from app.modules.insights import rules
from app.modules.insights.models import Insight
from app.modules.schemes.translate import _numbers
from app.modules.users.models import User

log = logging.getLogger(__name__)

FILTERS = {"savings": "savings", "spending": "spending", "goals": "goals"}


class _Phrase(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=2, max_length=400)


async def localize(title: str, body: str, language: str) -> tuple[str, str, str]:
    """(title, body, language actually used). Falls back to English on any doubt."""
    if language == "en":
        return title, body, "en"
    try:
        result = await llm_client.chat_completion(
            [{"role": "user", "content": render("insight_phrase", language_name=language_name(language),
                                               title_en=title, body_en=body)}],
            json_schema=_Phrase, temperature=0.2, max_tokens=250, timeout=60,
        )
    except (AIUnavailable, AIOutputError) as exc:
        log.warning("insight kept in English", extra={"error": repr(exc)})
        return title, body, "en"
    out = result.data
    if _numbers(f"{title} {body}") - _numbers(f"{out.title} {out.body}"):
        log.warning("insight rewrite changed numbers; kept English")
        return title, body, "en"
    return out.title.strip(), out.body.strip(), language


async def store(session: AsyncSession, user: User, candidates: list[rules.Candidate]) -> list[Insight]:
    """Insert the candidates that don't exist yet (by dedupe_key). Returns the new rows."""
    if not candidates:
        return []
    keys = [c.dedupe_key for c in candidates]
    existing = set((await session.execute(
        select(Insight.dedupe_key).where(Insight.user_id == user.id, Insight.dedupe_key.in_(keys))
    )).scalars())
    created = []
    for c in candidates:
        if c.dedupe_key in existing:
            continue
        existing.add(c.dedupe_key)
        title, body, language = await localize(c.title, c.body, user.preferred_language)
        row = (await session.execute(
            insert(Insight).values(
                user_id=user.id, code=c.code, type=c.type, tone=c.tone, filter_group=c.filter_group,
                title=title[:120], body=body[:400], language=language, cta_route=c.cta_route, payload=c.payload,
                dedupe_key=c.dedupe_key, expires_at=rules.expiry(),
            ).on_conflict_do_nothing(index_elements=["user_id", "dedupe_key"]).returning(Insight)
        )).scalar_one_or_none()
        if row is not None:
            created.append(row)
    await session.commit()
    if created:
        log.info("insights created", extra={"user_id": str(user.id), "codes": [i.code for i in created]})
    return created


async def generate_for_user(session: AsyncSession, user_id: uuid.UUID) -> list[Insight]:
    user = await session.get(User, user_id)
    if user is None or user.status != "active":
        return []
    created = await store(session, user, await rules.daily_candidates(session, user_id))
    # Scheme deadlines also go out as a notification (setting scheme_deadline_enabled).
    from app.modules.notifications import service as notifications

    for ins in created:
        if ins.code == "I08":
            await notifications.notify(session, user_id, "scheme_deadline", ins.title, ins.body, ins.cta_route,
                                       setting="scheme_deadline_enabled")
    return created


async def scheme_news(session: AsyncSession, user_id: uuid.UUID, scheme_ids: list) -> Insight | None:
    """I09 after a profile change made new schemes eligible."""
    user = await session.get(User, user_id)
    cand = rules.i09_new_schemes(scheme_ids)
    if user is None or cand is None:
        return None
    created = await store(session, user, [cand])
    return created[0] if created else None


# --- Feed --------------------------------------------------------------------------

def _visible():
    return or_(Insight.expires_at.is_(None), Insight.expires_at > datetime.now(timezone.utc))


async def list_insights(session: AsyncSession, user: User, filter_: str, limit: int, cursor: str | None):
    stmt = select(Insight).where(Insight.user_id == user.id, _visible())
    if filter_ in FILTERS:
        stmt = stmt.where(Insight.filter_group == FILTERS[filter_])
    if cursor:
        stmt = stmt.where(after_cursor([Insight.created_at, Insight.id],
                                       decode_cursor(cursor, [datetime.fromisoformat, uuid.UUID])))
    rows = list((await session.execute(
        stmt.order_by(Insight.created_at.desc(), Insight.id.desc()).limit(limit + 1)
    )).scalars())
    page = rows[:limit]
    return page, (encode_cursor([page[-1].created_at, page[-1].id]) if len(rows) > limit else None)


async def mark_read(session: AsyncSession, user: User, insight_id: uuid.UUID) -> None:
    result = await session.execute(
        update(Insight).where(Insight.id == insight_id, Insight.user_id == user.id).values(is_read=True)
    )
    if result.rowcount == 0:
        raise AppError("NOT_FOUND")
    await session.commit()


async def top_unread(session: AsyncSession, user_id: uuid.UUID, limit: int = 3) -> list[Insight]:
    return list((await session.execute(
        select(Insight).where(Insight.user_id == user_id, ~Insight.is_read, _visible())
        .order_by(Insight.created_at.desc()).limit(limit)
    )).scalars())
