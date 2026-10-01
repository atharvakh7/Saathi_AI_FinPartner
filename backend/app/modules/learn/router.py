"""/learn/* endpoints (spec §7.2, §7.4)."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.i18n import resolve_language
from app.core.security import get_current_user
from app.modules.learn import service, term_detector
from app.modules.learn.schemas import (
    CompleteOut,
    DetectedTerm,
    DetectIn,
    DetectOut,
    FeedbackIn,
    LessonDetail,
    LessonListItem,
    StatsOut,
    TermDetail,
    TermList,
)
from app.modules.users.models import User

router = APIRouter(prefix="/learn", tags=["learn"])

GlossaryCategory = Literal["basics", "investing", "savings", "insurance", "loans"]
LessonCategory = Literal["basics", "investing", "savings", "insurance"]


def _lang(request: Request, lang: str | None, user: User) -> str:
    return resolve_language(request, lang, fallback=user.preferred_language)


@router.get("/terms", response_model=TermList)
async def list_terms(
    request: Request,
    q: str | None = Query(default=None, max_length=80),
    category: GlossaryCategory | None = None,
    limit: int = Query(default=20, ge=1, le=50),
    lang: str | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    items = await service.search_terms(session, q, category, limit, _lang(request, lang, user))
    return TermList(items=items)


@router.get("/terms/{slug}", response_model=TermDetail)
async def get_term(
    slug: str, request: Request, lang: str | None = None,
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db),
):
    return await service.term_detail(session, user, slug, _lang(request, lang, user))


@router.post("/terms/{slug}/feedback", status_code=204)
async def term_feedback(
    slug: str, body: FeedbackIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> Response:
    await service.term_feedback(session, user, slug, body.helpful)
    return Response(status_code=204)


@router.post("/detect-terms", response_model=DetectOut)
async def detect_terms(body: DetectIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    spans = await term_detector.detect(session, body.text, body.language)
    return DetectOut(terms=[DetectedTerm(**s.__dict__) for s in spans])


@router.get("/lessons", response_model=list[LessonListItem])
async def list_lessons(
    request: Request, category: LessonCategory | None = None, lang: str | None = None,
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db),
):
    return await service.list_lessons(session, user, category, _lang(request, lang, user))


@router.get("/lessons/{lesson_id}", response_model=LessonDetail)
async def get_lesson(
    lesson_id: uuid.UUID, request: Request, lang: str | None = None,
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db),
):
    return await service.lesson_detail(session, user, lesson_id, _lang(request, lang, user))


@router.post("/lessons/{lesson_id}/complete", response_model=CompleteOut)
async def complete_lesson(
    lesson_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
):
    return await service.complete_lesson(session, user, lesson_id)


@router.get("/stats", response_model=StatsOut)
async def learning_stats(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.learning_stats(session, user)
