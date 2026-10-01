"""/memory endpoints (spec §4.7 S40, §7.4)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.modules.memory import service
from app.modules.users.models import User

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryFactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    category: str
    fact_text: str
    importance: int
    created_at: datetime


@router.get("", response_model=list[MemoryFactOut])
async def list_memory(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.list_facts(session, user)


@router.delete("/{fact_id}", status_code=204)
async def delete_memory(
    fact_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> Response:
    await service.delete_fact(session, user, fact_id)
    return Response(status_code=204)


@router.delete("", status_code=204)
async def delete_all_memory(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> Response:
    await service.delete_all_facts(session, user)
    return Response(status_code=204)
