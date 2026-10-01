"""/schemes/* endpoints (spec §4.7 S23–S27, §7.4)."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.i18n import resolve_language
from app.core.security import get_current_user
from app.modules.schemes import service
from app.modules.schemes.schemas import (
    CategoryOut,
    CheckIn,
    MatchesOut,
    MatchStatus,
    QuestionsOut,
    SchemeDetail,
    SchemePage,
    TrackingIn,
    TrackingOut,
)
from app.modules.users.models import User

router = APIRouter(prefix="/schemes", tags=["schemes"])

CategorySlug = Literal["health", "education", "housing", "employment", "agriculture", "women", "social-security"]


def _lang(request: Request, lang: str | None, user: User) -> str:
    return resolve_language(request, lang, fallback=user.preferred_language)


# Fixed paths come before /{scheme_id}.

@router.get("/categories", response_model=list[CategoryOut])
async def scheme_categories(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.categories(session, user)


@router.get("", response_model=SchemePage)
async def list_schemes(
    request: Request,
    category: CategorySlug | None = None,
    q: str | None = Query(default=None, max_length=80),
    status: MatchStatus | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    cursor: str | None = None,
    lang: str | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await service.list_schemes(
        session, user, category=category, q=q, status=status, limit=limit, cursor=cursor,
        language=_lang(request, lang, user),
    )


@router.get("/eligibility/questions", response_model=QuestionsOut)
async def eligibility_questions(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.questions(session, user)


@router.post("/eligibility/check", response_model=MatchesOut)
async def eligibility_check(
    body: CheckIn, request: Request, lang: str | None = None,
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db),
):
    return await service.check(session, user, body.answers, _lang(request, lang, user))


@router.get("/matches", response_model=MatchesOut)
async def scheme_matches(
    request: Request, lang: str | None = None,
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db),
):
    return await service.matches(session, user, _lang(request, lang, user))


@router.get("/{scheme_id}", response_model=SchemeDetail)
async def scheme_detail(
    scheme_id: uuid.UUID, request: Request, lang: str | None = None,
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db),
):
    return await service.detail(session, user, scheme_id, _lang(request, lang, user))


@router.put("/{scheme_id}/tracking", response_model=TrackingOut, responses={204: {"description": "Tracking cleared"}})
async def scheme_tracking(
    scheme_id: uuid.UUID, body: TrackingIn,
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db),
):
    status = await service.set_tracking(session, user, scheme_id, body.status)
    if status is None:
        return Response(status_code=204)
    return TrackingOut(status=status)
