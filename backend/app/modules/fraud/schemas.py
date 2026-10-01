"""Fraud Shield DTOs (spec §7.3 FraudCheckDTO, §7.4 /fraud/*)."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SourceApp = Literal["whatsapp", "sms", "other"]
Language = Literal["en", "hi", "mr", "ta"]


class AnalyzeTextIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=10, max_length=5000)
    source_app: SourceApp = "whatsapp"
    input_type: Literal["text", "shared_text"] = "text"
    language: Language | None = None  # null -> the user's preferred language


class ReasonOut(BaseModel):
    code: str
    key: str  # reason_key, for the app's own translations (spec §5.7 step 8)
    title: str
    text: str


class FraudCheckOut(BaseModel):
    id: uuid.UUID
    input_type: str
    source_app: str
    snippet: str
    risk_score: int
    verdict: Literal["safe", "suspicious", "dangerous"]
    summary: str
    advice: str
    reasons: list[ReasonOut]
    similar_reports_count: int
    reported: bool
    language: str
    created_at: datetime


class FraudCheckListItem(BaseModel):
    id: uuid.UUID
    snippet: str
    source_app: str
    input_type: str
    verdict: str
    risk_score: int
    created_at: datetime


class FraudCheckPage(BaseModel):
    items: list[FraudCheckListItem]
    next_cursor: str | None


class ReportOut(BaseModel):
    reported: bool
