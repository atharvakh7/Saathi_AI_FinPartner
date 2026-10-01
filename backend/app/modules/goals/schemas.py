"""Goal request/response bodies (spec §4.7 S17–S19, §7.3 GoalDTO, §7.4 goals)."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.core import enums
from app.core.types import Money

GoalCategory = Literal[enums.GOAL_CATEGORIES]  # type: ignore[valid-type]
GoalTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
Target = Annotated[Decimal, Field(gt=0, le=100_000_000, max_digits=12, decimal_places=2)]
Note = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]


class GoalIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: GoalTitle
    category: GoalCategory
    target_amount_inr: Target
    target_date: date | None = None
    current_amount_inr: Annotated[Decimal, Field(ge=0, le=100_000_000, max_digits=12, decimal_places=2)] = Decimal(0)


class GoalPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: GoalTitle | None = None
    target_amount_inr: Target | None = None
    target_date: date | None = None
    status: Literal["active", "paused", "cancelled"] | None = None


class ContributionIn(BaseModel):
    """Positive = add money, negative = withdraw (spec §7.4)."""

    model_config = ConfigDict(extra="forbid")
    amount_inr: Annotated[Decimal, Field(ge=-100_000_000, le=100_000_000, max_digits=12, decimal_places=2)]
    contributed_on: date | None = None
    note: Note | None = None


class Projection(BaseModel):
    monthly_rate_inr: Money
    projected_completion: date | None
    on_track: bool | None


class GoalOut(BaseModel):
    """GoalDTO."""

    id: uuid.UUID
    title: str
    category: str
    target_amount_inr: Money
    current_amount_inr: Money
    progress_pct: int
    target_date: date | None
    status: str
    projection: Projection


class ContributionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    amount_inr: Money
    contributed_on: date
    note: str | None


class GoalDetailOut(GoalOut):
    contributions: list[ContributionOut]


class GoalTemplateOut(BaseModel):
    slug: str
    title: str
    category: str
    default_target_inr: Money | None
