"""Admin request/response bodies (spec §7.4 "Admin endpoints"): snake_case DB columns, English text.

Length limits mirror the database columns, so bad input is a 422, never a database error.
"""

import uuid
from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from app.core import enums

Slug = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=80)]
Url = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^https?://\S+$", max_length=300)]


def _s(n: int, min_length: int = 1):
    return Annotated[str, StringConstraints(strip_whitespace=True, min_length=min_length, max_length=n)]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Schemes -----------------------------------------------------------------------

class RuleIn(_In):
    rule_key: Annotated[str, StringConstraints(pattern=r"^[a-z0-9_]{1,60}$")]
    field: _s(50)
    operator: Literal[enums.RULE_OPERATORS]  # type: ignore[valid-type]
    value: Any = None
    is_mandatory: bool = True
    explanation_en: _s(200)


class StepIn(_In):
    title_en: _s(100)
    description_en: _s(400)


class DocumentIn(_In):
    name: _s(120)
    is_mandatory: bool = True


class SchemeIn(_In):
    slug: Slug
    name_en: _s(150)
    level: Literal[enums.SCHEME_LEVELS]  # type: ignore[valid-type]
    state_code: Literal[enums.STATE_CODES] | None = None  # type: ignore[valid-type]
    category_slug: _s(30)
    ministry_or_dept: _s(120) | None = None
    benefit_type: Literal[enums.BENEFIT_TYPES]  # type: ignore[valid-type]
    benefit_summary_en: _s(300)
    description_en: _s(5000)
    application_mode_en: _s(200) | None = None
    official_url: Url
    source_url: Url | None = None  # defaults to official_url
    last_verified_on: date | None = None  # defaults to today
    deadline_on: date | None = None
    is_active: bool = True
    rules: list[RuleIn] = Field(min_length=1, max_length=20)
    steps: list[StepIn] = Field(min_length=1, max_length=10)
    documents: list[DocumentIn] = Field(min_length=1, max_length=15)

    @model_validator(mode="after")
    def _consistent(self):
        if self.level == "state" and not self.state_code:
            raise ValueError("state schemes need state_code")
        if self.level == "central" and self.state_code:
            raise ValueError("central schemes have no state_code")
        keys = [r.rule_key for r in self.rules]
        if len(keys) != len(set(keys)):
            raise ValueError("rule_key values must be unique")
        return self


class SchemeTranslationIn(_In):
    name: _s(200)
    benefit_summary: _s(600)
    description: _s(8000)
    steps: list[dict[Literal["title", "description"], _s(800)]]
    documents: list[_s(300)]
    rule_explanations: dict[str, _s(400)]


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    rule_key: str
    field: str
    operator: str
    value: Any
    is_mandatory: bool
    explanation_en: str


class StepOut(BaseModel):
    step_no: int
    title_en: str
    description_en: str


class DocumentOut(BaseModel):
    name: str
    is_mandatory: bool


class SchemeAdminOut(BaseModel):
    id: uuid.UUID
    slug: str
    name_en: str
    level: str
    state_code: str | None
    category_slug: str
    ministry_or_dept: str | None
    benefit_type: str
    benefit_summary_en: str
    description_en: str
    application_mode_en: str | None
    official_url: str
    source_url: str
    last_verified_on: date
    deadline_on: date | None
    is_active: bool
    rules: list[RuleOut]
    steps: list[StepOut]
    documents: list[DocumentOut]
    translations: dict[str, str]  # language -> "llm" | "human"


class TranslationOut(BaseModel):
    language: str
    generated_by: str
    reviewed: bool


# --- Glossary ----------------------------------------------------------------------

class GlossaryIn(_In):
    slug: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=60)]
    term_en: _s(80)
    aliases: list[_s(80)] = Field(default_factory=list, max_length=20)
    category: Literal[enums.GLOSSARY_CATEGORIES]  # type: ignore[valid-type]
    definition_en: _s(400)
    example_en: _s(400)
    analogy_en: _s(300)
    key_takeaway_en: _s(150)
    related_slugs: list[str] = Field(default_factory=list, max_length=10)
    video_id: uuid.UUID | None = None
    is_active: bool = True


class GlossaryTranslationIn(_In):
    term_local: _s(120)
    definition: _s(600)
    example: _s(600)
    analogy: _s(500)
    key_takeaway: _s(250)


class GlossaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slug: str
    term_en: str
    aliases: list[str]
    category: str
    definition_en: str
    example_en: str
    analogy_en: str
    key_takeaway_en: str
    related_slugs: list[str]
    video_id: uuid.UUID | None
    is_active: bool
    updated_at: datetime


# --- Lessons & videos --------------------------------------------------------------

class LessonIn(_In):
    slug: Slug
    category: Literal[enums.LESSON_CATEGORIES]  # type: ignore[valid-type]
    sort_order: int = Field(ge=0, le=1000)
    title_en: _s(120)
    duration_min: int = Field(ge=1, le=120)
    difficulty: Literal[enums.DIFFICULTIES]  # type: ignore[valid-type]
    body_md_en: _s(50_000, min_length=20)
    video_id: uuid.UUID | None = None
    xp_reward: int = Field(default=50, ge=0, le=1000)
    is_active: bool = True


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slug: str
    category: str
    sort_order: int
    title_en: str
    duration_min: int
    difficulty: str
    body_md_en: str
    video_id: uuid.UUID | None
    xp_reward: int
    is_active: bool
    updated_at: datetime


class VideoIn(_In):
    title: _s(120)
    language: Literal[enums.LANGUAGES]  # type: ignore[valid-type]
    duration_sec: int = Field(ge=1, le=3 * 3600)
    filename: _s(200)

    @field_validator("filename")
    @classmethod
    def _mp4(cls, v: str) -> str:
        if not v.lower().endswith(".mp4"):
            raise ValueError("videos must be .mp4 (stored as videos/{id}.mp4)")
        return v


class VideoUploadOut(BaseModel):
    id: uuid.UUID
    upload_url: str
    storage_key: str
    expires_in_sec: int


# --- Fraud patterns ----------------------------------------------------------------

class FraudPatternIn(_In):
    code: Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Z][A-Z0-9]{1,7}$")]
    description: _s(200)
    pattern_type: Literal[enums.FRAUD_PATTERN_TYPES]  # type: ignore[valid-type]
    patterns: list[_s(500)] = Field(min_length=1, max_length=50)
    weight: int = Field(ge=-100, le=100)
    requires_codes: list[Annotated[str, StringConstraints(pattern=r"^!?[A-Z][A-Z0-9]{1,7}$")]] | None = None
    reason_key: _s(40) | None = None
    reason_title_en: _s(80) | None = None
    reason_text_en: _s(200) | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def _consistent(self):
        if self.weight > 0 and not (self.reason_key and self.reason_title_en and self.reason_text_en):
            raise ValueError("positive-weight rules need reason_key, reason_title_en and reason_text_en")
        if self.pattern_type == "negative" and self.weight > 0:
            raise ValueError("negative rules must have weight <= 0")
        return self


class FraudPatternOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    description: str
    pattern_type: str
    patterns: list[str]
    weight: int
    requires_codes: list[str] | None
    reason_key: str | None
    reason_title_en: str | None
    reason_text_en: str | None
    is_active: bool
    updated_at: datetime
