"""/notifications endpoints (spec §4.7 S13, §7.4)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.modules.notifications import service
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    id: uuid.UUID
    kind: str
    title: str
    body: str
    data: dict | None
    read: bool
    created_at: datetime


class NotificationPage(BaseModel):
    items: list[NotificationOut]
    next_cursor: str | None


@router.get("", response_model=NotificationPage)
async def list_notifications(
    limit: int = Query(default=30, ge=1, le=100), cursor: str | None = None,
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db),
):
    rows, next_cursor = await service.list_notifications(session, user.id, limit, cursor)
    return NotificationPage(
        items=[NotificationOut(id=n.id, kind=n.kind, title=n.title, body=n.body, data=n.data,
                               read=n.read_at is not None, created_at=n.created_at) for n in rows],
        next_cursor=next_cursor,
    )


@router.post("/read-all", status_code=204)
async def read_all(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> Response:
    await service.mark_all_read(session, user.id)
    return Response(status_code=204)


@router.post("/{notification_id}/read", status_code=204)
async def read_one(notification_id: uuid.UUID, user: User = Depends(get_current_user),
                   session: AsyncSession = Depends(get_db)) -> Response:
    await service.mark_read(session, user.id, notification_id)
    return Response(status_code=204)
