"""Glossary, lessons, videos, progress, stats, feedback (spec §5.8, §6.1)."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core import enums
from app.core.db import Base, CreatedAt, Timestamps, UpdatedAt, UUIDPk, check_in, check_range


class Video(UUIDPk, CreatedAt, Base):
    __tablename__ = "videos"
    __table_args__ = (check_in("language", enums.LANGUAGES), check_range("duration_sec", 0))

    title: Mapped[str] = mapped_column(String(120), nullable=False)
    language: Mapped[str] = mapped_column(String(2), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(200), nullable=False)
    thumbnail_key: Mapped[str | None] = mapped_column(String(200))
    duration_sec: Mapped[int] = mapped_column(Integer, nullable=False)


class GlossaryTerm(UUIDPk, Timestamps, Base):
    __tablename__ = "glossary_terms"
    __table_args__ = (check_in("category", enums.GLOSSARY_CATEGORIES),)

    slug: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    term_en: Mapped[str] = mapped_column(String(80), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default=text("'{}'"), default=list)
    category: Mapped[str] = mapped_column(String(10), nullable=False)
    definition_en: Mapped[str] = mapped_column(String(400), nullable=False)
    example_en: Mapped[str] = mapped_column(String(400), nullable=False)
    analogy_en: Mapped[str] = mapped_column(String(300), nullable=False)
    key_takeaway_en: Mapped[str] = mapped_column(String(150), nullable=False)
    related_slugs: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'"), default=list
    )
    video_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("videos.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)


class GlossaryTranslation(UUIDPk, Base):
    __tablename__ = "glossary_translations"
    __table_args__ = (
        check_in("language", enums.TRANSLATION_LANGUAGES),
        check_in("generated_by", enums.GENERATED_BY),
        UniqueConstraint("term_id", "language"),
    )

    term_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("glossary_terms.id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[str] = mapped_column(String(2), nullable=False)
    term_local: Mapped[str] = mapped_column(String(120), nullable=False)
    definition: Mapped[str] = mapped_column(String(600), nullable=False)
    example: Mapped[str] = mapped_column(String(600), nullable=False)
    analogy: Mapped[str] = mapped_column(String(500), nullable=False)
    key_takeaway: Mapped[str] = mapped_column(String(250), nullable=False)
    generated_by: Mapped[str] = mapped_column(String(5), nullable=False)
    reviewed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), default=False)


class Lesson(UUIDPk, Timestamps, Base):
    __tablename__ = "lessons"
    __table_args__ = (
        check_in("category", enums.LESSON_CATEGORIES),
        check_in("difficulty", enums.DIFFICULTIES),
        check_range("duration_min", 1),
        check_range("xp_reward", 0),
    )

    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(10), nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title_en: Mapped[str] = mapped_column(String(120), nullable=False)
    duration_min: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(6), nullable=False)
    body_md_en: Mapped[str] = mapped_column(Text, nullable=False)
    video_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("videos.id", ondelete="SET NULL"))
    xp_reward: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("50"), default=50)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)


class LessonTranslation(UUIDPk, Base):
    __tablename__ = "lesson_translations"
    __table_args__ = (
        check_in("language", enums.TRANSLATION_LANGUAGES),
        check_in("generated_by", enums.GENERATED_BY),
        UniqueConstraint("lesson_id", "language"),
    )

    lesson_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    language: Mapped[str] = mapped_column(String(2), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body_md: Mapped[str] = mapped_column(Text, nullable=False)
    generated_by: Mapped[str] = mapped_column(String(5), nullable=False)
    reviewed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), default=False)


class LessonProgress(UUIDPk, Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (
        check_in("status", ("completed",)),
        UniqueConstraint("user_id", "lesson_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(9), nullable=False, server_default="completed", default="completed")
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UserLearningStats(UpdatedAt, Base):
    __tablename__ = "user_learning_stats"
    __table_args__ = (
        check_range("xp", 0),
        check_range("level", 1),
        check_range("streak_days", 0),
        check_range("longest_streak", 0),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    xp: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"), default=0)
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("1"), default=1)
    streak_days: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"), default=0)
    longest_streak: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"), default=0)
    last_active_on: Mapped[date | None] = mapped_column(Date)


class TermFeedback(UUIDPk, CreatedAt, Base):
    __tablename__ = "term_feedback"
    __table_args__ = (UniqueConstraint("user_id", "term_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    term_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("glossary_terms.id", ondelete="CASCADE"), nullable=False
    )
    helpful: Mapped[bool] = mapped_column(Boolean, nullable=False)
