"""/goals/* endpoints (spec §7.2, §7.4)."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.modules.goals import service
from app.modules.goals.schemas import ContributionIn, GoalDetailOut, GoalIn, GoalOut, GoalPatch, GoalTemplateOut
from app.modules.users.models import User

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("/templates", response_model=list[GoalTemplateOut])
async def goal_templates(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.list_templates(session)


@router.get("", response_model=list[GoalOut])
async def list_goals(
    status: Literal["active", "completed", "all"] = "active",
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await service.list_goals(session, user, status)


@router.post("", response_model=GoalOut, status_code=201)
async def create_goal(body: GoalIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.create_goal(session, user, body)


@router.get("/{goal_id}", response_model=GoalDetailOut)
async def get_goal(goal_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await service.goal_detail(session, user, goal_id)


@router.patch("/{goal_id}", response_model=GoalOut)
async def update_goal(
    goal_id: uuid.UUID, body: GoalPatch, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
):
    return await service.update_goal(session, user, goal_id, body)


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(
    goal_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> Response:
    await service.delete_goal(session, user, goal_id)
    return Response(status_code=204)


@router.post("/{goal_id}/contributions", response_model=GoalOut, status_code=201)
async def add_contribution(
    goal_id: uuid.UUID, body: ContributionIn, user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await service.add_contribution(session, user, goal_id, body)
