"""Scheme Scout DTOs (spec §7.3 SchemeSummaryDTO, §7.4 /schemes/*)."""

import uuid
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

MatchStatus = Literal["eligible", "possibly_eligible", "not_eligible"]
TrackingStatus = Literal["saved", "applied", "dismissed"]


class CategoryOut(BaseModel):
    slug: str
    name: str
    icon: str
    count: int


class SchemeSummary(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    level: str
    state_code: str | None
    category_slug: str
    benefit_summary: str
    match_status: MatchStatus | None


class SchemePage(BaseModel):
    items: list[SchemeSummary]
    next_cursor: str | None


class QuestionOut(BaseModel):
    field: str
    type: Literal["boolean", "number", "enum"]
    options: list[str] | None
    affects_count: int


class QuestionsOut(BaseModel):
    questions: list[QuestionOut]


class CheckIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # field -> value; null = "Not sure" (not persisted)
    answers: dict[str, Any] = Field(max_length=40)


class FailedReason(BaseModel):
    rule_key: str
    field: str
    explanation: str


class MatchItem(BaseModel):
    scheme: SchemeSummary
    status: MatchStatus
    missing_fields: list[str]
    # (Suggested) why a not-eligible scheme failed, for S25 "Show schemes I don't qualify for".
    reasons: list[FailedReason]


class MatchesOut(BaseModel):
    eligible_count: int
    possibly_eligible_count: int
    total: int  # eligible + possibly eligible
    items: list[MatchItem]


class SchemeInfo(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    level: str
    state_code: str | None
    category_slug: str
    ministry_or_dept: str | None
    benefit_type: str
    benefit_summary: str
    description: str
    application_mode: str | None
    official_url: str
    last_verified_on: date
    deadline_on: date | None
    translation_source: Literal["llm", "human"] | None


class RuleResultOut(BaseModel):
    rule_key: str
    field: str
    result: Literal["pass", "fail", "unknown"]
    explanation: str


class MatchOut(BaseModel):
    status: MatchStatus
    rules: list[RuleResultOut]


class StepOut(BaseModel):
    step_no: int
    title: str
    description: str


class DocumentOut(BaseModel):
    name: str
    is_mandatory: bool


class SchemeDetail(BaseModel):
    scheme: SchemeInfo
    match: MatchOut
    steps: list[StepOut]
    documents: list[DocumentOut]
    tracking_status: TrackingStatus | None
    language: str  # language the content is actually in ("en" when no translation was available)
    disclaimer: str


class TrackingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: TrackingStatus | None


class TrackingOut(BaseModel):
    status: TrackingStatus
