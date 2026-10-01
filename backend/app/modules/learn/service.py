"""Glossary, lessons, XP and streaks (spec §5.8, §7.4 /learn/*).

Content is served in the requested language when a translation exists, else in English.
XP: completing a lesson awards its xp_reward once; level = max(1, floor(xp / 100)).
Streak: completing a lesson or viewing a term counts as activity for the day (IST).
"""

import re
import uuid
from datetime import date

from sqlalchemy import func, or_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError
from app.core.storage import VIDEO_URL_TTL_SEC, presigned_get
from app.core.types import today_ist
from app.modules.learn.models import (
    GlossaryTerm,
    GlossaryTranslation,
    Lesson,
    LessonProgress,
    LessonTranslation,
    TermFeedback,
    UserLearningStats,
    Video,
)
from app.modules.learn.schemas import (
    CompleteOut,
    LessonDetail,
    LessonListItem,
    RelatedTerm,
    StatsBrief,
    StatsOut,
    TermDetail,
    TermListItem,
    VideoOut,
)
from app.modules.users.models import User

SHORT_MAX = 120


def level_for(xp: int) -> int:
    return max(1, xp // 100)


def _first_sentence(text: str) -> str:
    sentence = re.split(r"(?<=[.!?।])\s", text.strip(), maxsplit=1)[0]
    return sentence if len(sentence) <= SHORT_MAX else sentence[: SHORT_MAX - 1].rstrip() + "…"


def _video_out(video: Video | None) -> VideoOut | None:
    if video is None:
        return None
    return VideoOut(
        url=presigned_get(settings.S3_BUCKET_MEDIA, video.storage_key, VIDEO_URL_TTL_SEC),
        duration_sec=video.duration_sec,
        thumbnail_url=presigned_get(settings.S3_BUCKET_MEDIA, video.thumbnail_key, VIDEO_URL_TTL_SEC)
        if video.thumbnail_key else None,
    )


# --- Streak & XP -------------------------------------------------------------------

async def _locked_stats(session: AsyncSession, user_id: uuid.UUID) -> UserLearningStats:
    await session.execute(insert(UserLearningStats).values(user_id=user_id).on_conflict_do_nothing())
    return (
        await session.execute(select(UserLearningStats).where(UserLearningStats.user_id == user_id).with_for_update())
    ).scalar_one()


def _apply_activity(stats: UserLearningStats, today: date) -> None:
    """§5.8: yesterday -> +1, today -> unchanged, otherwise restart at 1."""
    last = stats.last_active_on
    if last == today:
        return
    stats.streak_days = stats.streak_days + 1 if last is not None and (today - last).days == 1 else 1
    stats.longest_streak = max(stats.longest_streak, stats.streak_days)
    stats.last_active_on = today


def effective_streak(stats: UserLearningStats | None, today: date) -> int:
    """A streak only counts while it's alive: last activity today or yesterday."""
    if stats is None or stats.last_active_on is None or (today - stats.last_active_on).days > 1:
        return 0
    return stats.streak_days


async def record_activity(session: AsyncSession, user_id: uuid.UUID) -> None:
    stats = await _locked_stats(session, user_id)
    _apply_activity(stats, today_ist())
    await session.commit()


# --- Glossary ----------------------------------------------------------------------

def _localized_term(term: GlossaryTerm, tr: GlossaryTranslation | None) -> dict:
    if tr is None:
        return {"term": term.term_en, "definition": term.definition_en, "example": term.example_en,
                "analogy": term.analogy_en, "key_takeaway": term.key_takeaway_en, "translation_source": None}
    return {"term": tr.term_local, "definition": tr.definition, "example": tr.example, "analogy": tr.analogy,
            "key_takeaway": tr.key_takeaway, "translation_source": tr.generated_by}


def _with_translation(language: str):
    return (
        select(GlossaryTerm, GlossaryTranslation)
        .outerjoin(
            GlossaryTranslation,
            (GlossaryTranslation.term_id == GlossaryTerm.id) & (GlossaryTranslation.language == language),
        )
        .where(GlossaryTerm.is_active)
    )


async def search_terms(
    session: AsyncSession, q: str | None, category: str | None, limit: int, language: str
) -> list[TermListItem]:
    stmt = _with_translation(language)
    if category:
        stmt = stmt.where(GlossaryTerm.category == category)
    q = (q or "").strip()
    if q:
        like = f"%{q}%"
        alias_match = text("EXISTS (SELECT 1 FROM unnest(glossary_terms.aliases) a WHERE a ILIKE :like)")
        stmt = stmt.where(
            or_(
                GlossaryTerm.term_en.ilike(like),
                GlossaryTerm.slug.ilike(like),
                GlossaryTranslation.term_local.ilike(like),
                alias_match,
            )
        ).params(like=like)
        # Prefix matches first ("SIP" before "Insurance Premium" for q="sip")
        stmt = stmt.order_by(
            (~GlossaryTerm.term_en.ilike(f"{q}%") & ~func.coalesce(GlossaryTranslation.term_local, "").ilike(f"{q}%")),
            func.lower(func.coalesce(GlossaryTranslation.term_local, GlossaryTerm.term_en)),
        )
    else:
        stmt = stmt.order_by(func.lower(func.coalesce(GlossaryTranslation.term_local, GlossaryTerm.term_en)))
    rows = (await session.execute(stmt.limit(limit))).all()
    out = []
    for term, tr in rows:
        loc = _localized_term(term, tr)
        out.append(TermListItem(slug=term.slug, term=loc["term"], category=term.category,
                                short=_first_sentence(loc["definition"])))
    return out


async def term_detail(session: AsyncSession, user: User, slug: str, language: str) -> TermDetail:
    row = (await session.execute(_with_translation(language).where(GlossaryTerm.slug == slug))).first()
    if row is None:
        raise AppError("NOT_FOUND")
    term, tr = row
    related_rows = (
        await session.execute(_with_translation(language).where(GlossaryTerm.slug.in_(term.related_slugs or [])))
    ).all()
    order = {s: i for i, s in enumerate(term.related_slugs or [])}
    related = sorted(
        (RelatedTerm(slug=t.slug, term=_localized_term(t, r)["term"]) for t, r in related_rows),
        key=lambda x: order[x.slug],
    )
    video = await session.get(Video, term.video_id) if term.video_id else None
    detail = TermDetail(
        slug=term.slug, term_en=term.term_en, category=term.category,
        language=language if tr is not None else "en",
        related=related, video=_video_out(video), **_localized_term(term, tr),
    )
    await record_activity(session, user.id)  # viewing a term counts for the streak (§5.8)
    return detail


async def term_feedback(session: AsyncSession, user: User, slug: str, helpful: bool) -> None:
    term_id = (
        await session.execute(select(GlossaryTerm.id).where(GlossaryTerm.slug == slug, GlossaryTerm.is_active))
    ).scalar_one_or_none()
    if term_id is None:
        raise AppError("NOT_FOUND")
    stmt = insert(TermFeedback).values(user_id=user.id, term_id=term_id, helpful=helpful)
    stmt = stmt.on_conflict_do_update(index_elements=["user_id", "term_id"], set_={"helpful": helpful})
    await session.execute(stmt)
    await session.commit()


# --- Lessons -----------------------------------------------------------------------

def _lesson_with(language: str, user_id: uuid.UUID):
    return (
        select(Lesson, LessonTranslation, LessonProgress.id.is_not(None).label("completed"))
        .outerjoin(LessonTranslation,
                   (LessonTranslation.lesson_id == Lesson.id) & (LessonTranslation.language == language))
        .outerjoin(LessonProgress, (LessonProgress.lesson_id == Lesson.id) & (LessonProgress.user_id == user_id))
        .where(Lesson.is_active)
    )


async def list_lessons(session: AsyncSession, user: User, category: str | None, language: str) -> list[LessonListItem]:
    stmt = _lesson_with(language, user.id)
    if category:
        stmt = stmt.where(Lesson.category == category)
    rows = (await session.execute(stmt.order_by(Lesson.sort_order))).all()
    return [
        LessonListItem(id=lesson.id, slug=lesson.slug, category=lesson.category,
                       title=tr.title if tr else lesson.title_en, duration_min=lesson.duration_min,
                       difficulty=lesson.difficulty, xp_reward=lesson.xp_reward, completed=bool(done))
        for lesson, tr, done in rows
    ]


async def lesson_detail(session: AsyncSession, user: User, lesson_id: uuid.UUID, language: str) -> LessonDetail:
    row = (await session.execute(_lesson_with(language, user.id).where(Lesson.id == lesson_id))).first()
    if row is None:
        raise AppError("NOT_FOUND")
    lesson, tr, done = row
    video = await session.get(Video, lesson.video_id) if lesson.video_id else None
    return LessonDetail(
        id=lesson.id, slug=lesson.slug, category=lesson.category,
        title=tr.title if tr else lesson.title_en, body_md=tr.body_md if tr else lesson.body_md_en,
        duration_min=lesson.duration_min, difficulty=lesson.difficulty, xp_reward=lesson.xp_reward,
        completed=bool(done), language=language if tr else "en", video=_video_out(video),
        translation_source=tr.generated_by if tr else None,
    )


async def complete_lesson(session: AsyncSession, user: User, lesson_id: uuid.UUID) -> CompleteOut:
    lesson = await session.get(Lesson, lesson_id)
    if lesson is None or not lesson.is_active:
        raise AppError("NOT_FOUND")
    stats = await _locked_stats(session, user.id)  # serializes double taps
    awarded = 0
    try:
        async with session.begin_nested():
            session.add(LessonProgress(user_id=user.id, lesson_id=lesson.id))
        awarded = lesson.xp_reward
    except IntegrityError:
        awarded = 0  # already completed: no XP the second time (spec §7.4)
    stats.xp += awarded
    stats.level = level_for(stats.xp)
    _apply_activity(stats, today_ist())
    await session.commit()
    return CompleteOut(xp_awarded=awarded, stats=StatsBrief(xp=stats.xp, level=stats.level,
                                                            streak_days=effective_streak(stats, today_ist())))


async def learning_stats(session: AsyncSession, user: User) -> StatsOut:
    stats = await session.get(UserLearningStats, user.id)
    completed = (
        await session.execute(
            select(func.count(LessonProgress.id))
            .join(Lesson, Lesson.id == LessonProgress.lesson_id)
            .where(LessonProgress.user_id == user.id, Lesson.is_active)
        )
    ).scalar_one()
    total = (await session.execute(select(func.count(Lesson.id)).where(Lesson.is_active))).scalar_one()
    return StatsOut(
        xp=stats.xp if stats else 0,
        level=stats.level if stats else 1,
        streak_days=effective_streak(stats, today_ist()),
        longest_streak=stats.longest_streak if stats else 0,
        completed_lessons=completed,
        total_lessons=total,
    )
