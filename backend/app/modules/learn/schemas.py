"""Learn request/response bodies (spec §4.7 S32–S34, §7.4 /learn/*)."""

import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints


class TermListItem(BaseModel):
    slug: str
    term: str
    category: str
    short: str


class TermList(BaseModel):
    items: list[TermListItem]


class RelatedTerm(BaseModel):
    slug: str
    term: str


class VideoOut(BaseModel):
    url: str
    duration_sec: int
    thumbnail_url: str | None


class TermDetail(BaseModel):
    slug: str
    term: str
    term_en: str
    category: str
    language: str
    definition: str
    example: str
    analogy: str
    key_takeaway: str
    related: list[RelatedTerm]
    video: VideoOut | None
    translation_source: Literal["llm", "human"] | None  # None = English original


class FeedbackIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    helpful: bool


class DetectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: Annotated[str, StringConstraints(min_length=1, max_length=5000)]
    language: Literal["en", "hi", "mr", "ta"] = "en"


class DetectedTerm(BaseModel):
    slug: str
    surface: str
    start: int
    end: int


class DetectOut(BaseModel):
    terms: list[DetectedTerm]


class LessonListItem(BaseModel):
    id: uuid.UUID
    slug: str
    category: str
    title: str
    duration_min: int
    difficulty: str
    xp_reward: int
    completed: bool


class LessonDetail(BaseModel):
    id: uuid.UUID
    slug: str
    category: str
    title: str
    body_md: str
    duration_min: int
    difficulty: str
    xp_reward: int
    completed: bool
    language: str
    video: VideoOut | None
    translation_source: Literal["llm", "human"] | None


class StatsBrief(BaseModel):
    xp: int
    level: int
    streak_days: int


class CompleteOut(BaseModel):
    xp_awarded: int
    stats: StatsBrief


class StatsOut(BaseModel):
    xp: int
    level: int
    streak_days: int
    longest_streak: int
    completed_lessons: int
    total_lessons: int
