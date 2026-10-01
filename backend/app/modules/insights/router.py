"""/insights endpoints (spec §4.7 S11, §7.4) and the event hooks that schedule insight runs."""

import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import events
from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.jobs import dispatch
from app.modules.insights import service
from app.modules.users.models import User

router = APIRouter(prefix="/insights", tags=["insights"])


class InsightOut(BaseModel):
    """InsightDTO (spec §7.3); `payload` lets the app use its own `insight.<code>` strings."""

    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    tone: str
    filter_group: str
    title: str
    body: str
    cta_route: str | None
    is_read: bool
    language: str
    payload: dict | None
    created_at: datetime


class InsightPage(BaseModel):
    items: list[InsightOut]
    next_cursor: str | None


@router.get("", response_model=InsightPage)
async def list_insights(
    filter: Literal["all", "savings", "spending", "goals"] = "all",
    limit: int = Query(default=30, ge=1, le=100), cursor: str | None = None,
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db),
):
    items, next_cursor = await service.list_insights(session, user, filter, limit, cursor)
    return InsightPage(items=items, next_cursor=next_cursor)


@router.post("/{insight_id}/read", status_code=204)
async def mark_read(insight_id: uuid.UUID, user: User = Depends(get_current_user),
                    session: AsyncSession = Depends(get_db)) -> Response:
    await service.mark_read(session, user, insight_id)
    return Response(status_code=204)


# --- Hooks (spec §5.9: after transaction writes, debounced; first run after onboarding) ---

@events.on(events.TRANSACTIONS_CHANGED)
async def _after_transactions(user_id: uuid.UUID) -> None:
    await dispatch.enqueue_debounced("insights.generate_user", str(user_id), settings.INSIGHTS_DEBOUNCE_SEC)


@events.on(events.ONBOARDING_COMPLETED)
async def _after_onboarding(user_id: uuid.UUID) -> None:
    await dispatch.enqueue("insights.generate_user", user_id)
