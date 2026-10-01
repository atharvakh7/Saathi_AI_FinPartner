"""Admin content management (spec F19, §7.4 "Admin endpoints").

Every write clears the caches that depend on it (spec): glossary -> term detector version (and the
chat's term vectors); fraud patterns -> `fraud:patterns`; schemes -> queues `schemes.recompute_all`.

When an admin changes English content, machine translations of it (generated_by='llm') are deleted
so the translate jobs regenerate them; human translations are kept but marked unreviewed.
"""

import logging
import re
import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError
from app.core.storage import presigned_put
from app.core.types import today_ist
from app.jobs import dispatch
from app.modules.admin.schemas import (
    DocumentOut,
    FraudPatternIn,
    GlossaryIn,
    GlossaryTranslationIn,
    LessonIn,
    RuleOut,
    SchemeAdminOut,
    SchemeIn,
    SchemeTranslationIn,
    StepOut,
    VideoIn,
    VideoUploadOut,
)
from app.modules.fraud import rules as fraud_rules
from app.modules.fraud.models import FraudPattern
from app.modules.learn import term_detector
from app.modules.learn.models import GlossaryTerm, GlossaryTranslation, Lesson, LessonTranslation, Video
from app.modules.schemes.field_registry import validate_rule
from app.modules.schemes.models import (
    Scheme,
    SchemeCategory,
    SchemeDocument,
    SchemeEligibilityRule,
    SchemeStep,
    SchemeTranslation,
)

log = logging.getLogger(__name__)

UPLOAD_URL_TTL_SEC = 3600


def _invalid(details: list[dict]) -> AppError:
    return AppError("VALIDATION_ERROR", details=details)


async def _commit_or_conflict(session: AsyncSession, what: str) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if "unique" in str(exc.orig).lower() or "duplicate" in str(exc.orig).lower():
            raise AppError("CONFLICT", f"A {what} with this slug/code already exists.") from exc
        raise


async def _ensure_unique(session: AsyncSession, model, column, value, exclude_id: uuid.UUID | None, what: str):
    stmt = select(model.id).where(column == value)
    if exclude_id is not None:
        stmt = stmt.where(model.id != exclude_id)
    if (await session.execute(stmt)).first():
        raise AppError("CONFLICT", f"A {what} with this slug/code already exists.")


# --- Schemes -----------------------------------------------------------------------

async def _validate_scheme(session: AsyncSession, body: SchemeIn) -> None:
    errors = []
    if await session.get(SchemeCategory, body.category_slug) is None:
        errors.append({"field": "category_slug", "issue": f"unknown category '{body.category_slug}'"})
    for i, r in enumerate(body.rules):
        err = validate_rule(r.field, r.operator, r.value)
        if err:
            errors.append({"field": f"rules.{i}", "issue": err})
    if body.level == "state" and not any(
        r.field == "state_code" and r.operator == "eq" and r.value == body.state_code and r.is_mandatory
        for r in body.rules
    ):
        errors.append({"field": "rules", "issue": f"a state scheme needs a mandatory rule state_code eq {body.state_code}"})
    if errors:
        raise _invalid(errors)


async def scheme_out(session: AsyncSession, scheme: Scheme) -> SchemeAdminOut:
    rules = (await session.execute(
        select(SchemeEligibilityRule).where(SchemeEligibilityRule.scheme_id == scheme.id)
        .order_by(SchemeEligibilityRule.rule_key))).scalars()
    steps = (await session.execute(
        select(SchemeStep).where(SchemeStep.scheme_id == scheme.id).order_by(SchemeStep.step_no))).scalars()
    docs = (await session.execute(
        select(SchemeDocument).where(SchemeDocument.scheme_id == scheme.id)
        .order_by(SchemeDocument.sort_order, SchemeDocument.document_name_en))).scalars()
    trs = (await session.execute(
        select(SchemeTranslation.language, SchemeTranslation.generated_by)
        .where(SchemeTranslation.scheme_id == scheme.id))).all()
    return SchemeAdminOut(
        **{c: getattr(scheme, c) for c in (
            "id", "slug", "name_en", "level", "state_code", "category_slug", "ministry_or_dept", "benefit_type",
            "benefit_summary_en", "description_en", "application_mode_en", "official_url", "source_url",
            "last_verified_on", "deadline_on", "is_active")},
        rules=[RuleOut.model_validate(r) for r in rules],
        steps=[StepOut(step_no=s.step_no, title_en=s.title_en, description_en=s.description_en) for s in steps],
        documents=[DocumentOut(name=d.document_name_en, is_mandatory=d.is_mandatory) for d in docs],
        translations=dict(trs),
    )


async def _write_children(session: AsyncSession, scheme_id: uuid.UUID, body: SchemeIn) -> None:
    for model in (SchemeEligibilityRule, SchemeStep, SchemeDocument):
        await session.execute(delete(model).where(model.scheme_id == scheme_id))
    session.add_all([SchemeEligibilityRule(scheme_id=scheme_id, **r.model_dump()) for r in body.rules])
    session.add_all([SchemeStep(scheme_id=scheme_id, step_no=i, **s.model_dump())
                     for i, s in enumerate(body.steps, start=1)])
    session.add_all([SchemeDocument(scheme_id=scheme_id, document_name_en=d.name, is_mandatory=d.is_mandatory,
                                    sort_order=i) for i, d in enumerate(body.documents)])


def _scheme_columns(body: SchemeIn) -> dict:
    data = body.model_dump(exclude={"rules", "steps", "documents"})
    data["source_url"] = data["source_url"] or data["official_url"]
    data["last_verified_on"] = data["last_verified_on"] or today_ist()
    return data


async def _schemes_changed() -> None:
    await dispatch.enqueue("schemes.recompute_all")


async def create_scheme(session: AsyncSession, body: SchemeIn) -> SchemeAdminOut:
    await _validate_scheme(session, body)
    await _ensure_unique(session, Scheme, Scheme.slug, body.slug, None, "scheme")
    scheme = Scheme(**_scheme_columns(body))
    session.add(scheme)
    await session.flush()
    await _write_children(session, scheme.id, body)
    await _commit_or_conflict(session, "scheme")
    await session.refresh(scheme)
    await _schemes_changed()
    return await scheme_out(session, scheme)


async def _get(session: AsyncSession, model, obj_id: uuid.UUID):
    obj = await session.get(model, obj_id)
    if obj is None:
        raise AppError("NOT_FOUND")
    return obj


async def replace_scheme(session: AsyncSession, scheme_id: uuid.UUID, body: SchemeIn) -> SchemeAdminOut:
    scheme = await _get(session, Scheme, scheme_id)
    await _validate_scheme(session, body)
    await _ensure_unique(session, Scheme, Scheme.slug, body.slug, scheme_id, "scheme")
    for key, value in _scheme_columns(body).items():
        setattr(scheme, key, value)
    await _write_children(session, scheme.id, body)
    # English changed: machine translations are regenerated; human ones need a fresh review.
    await session.execute(delete(SchemeTranslation).where(SchemeTranslation.scheme_id == scheme_id,
                                                          SchemeTranslation.generated_by == "llm"))
    await session.execute(update(SchemeTranslation).where(SchemeTranslation.scheme_id == scheme_id)
                          .values(reviewed=False))
    await _commit_or_conflict(session, "scheme")
    await session.refresh(scheme)
    await _schemes_changed()
    return await scheme_out(session, scheme)


async def deactivate_scheme(session: AsyncSession, scheme_id: uuid.UUID) -> None:
    scheme = await _get(session, Scheme, scheme_id)
    scheme.is_active = False
    await session.commit()
    await _schemes_changed()


async def set_scheme_translation(session: AsyncSession, scheme_id: uuid.UUID, language: str,
                                 body: SchemeTranslationIn) -> dict:
    await _get(session, Scheme, scheme_id)
    n_steps = (await session.execute(select(func.count()).where(SchemeStep.scheme_id == scheme_id))).scalar_one()
    n_docs = (await session.execute(select(func.count()).where(SchemeDocument.scheme_id == scheme_id))).scalar_one()
    keys = set((await session.execute(
        select(SchemeEligibilityRule.rule_key).where(SchemeEligibilityRule.scheme_id == scheme_id))).scalars())
    errors = []
    if len(body.steps) != n_steps or any(set(s) != {"title", "description"} for s in body.steps):
        errors.append({"field": "steps", "issue": f"need {n_steps} steps, each with title and description"})
    if len(body.documents) != n_docs:
        errors.append({"field": "documents", "issue": f"need {n_docs} documents"})
    if set(body.rule_explanations) != keys:
        errors.append({"field": "rule_explanations", "issue": f"need exactly the rule keys {sorted(keys)}"})
    if errors:
        raise _invalid(errors)
    stmt = insert(SchemeTranslation).values(scheme_id=scheme_id, language=language, content=body.model_dump(),
                                            generated_by="human", reviewed=True)
    stmt = stmt.on_conflict_do_update(index_elements=["scheme_id", "language"], set_={
        "content": stmt.excluded.content, "generated_by": "human", "reviewed": True, "updated_at": func.now()})
    await session.execute(stmt)
    await session.commit()
    return {"language": language, "generated_by": "human", "reviewed": True}


# --- Glossary ----------------------------------------------------------------------

async def _validate_glossary(session: AsyncSession, body: GlossaryIn) -> None:
    errors = []
    if body.related_slugs:
        known = set((await session.execute(
            select(GlossaryTerm.slug).where(GlossaryTerm.slug.in_(body.related_slugs)))).scalars())
        missing = sorted(set(body.related_slugs) - known - {body.slug})
        if missing or body.slug in body.related_slugs:
            errors.append({"field": "related_slugs", "issue": f"unknown or self references: {missing or [body.slug]}"})
    if body.video_id and await session.get(Video, body.video_id) is None:
        errors.append({"field": "video_id", "issue": "unknown video"})
    if errors:
        raise _invalid(errors)


async def _glossary_changed() -> None:
    await term_detector.invalidate()
    from app.modules.chat import tools  # in-process cache of glossary embeddings

    tools._term_vectors.clear()


async def create_term(session: AsyncSession, body: GlossaryIn) -> GlossaryTerm:
    await _validate_glossary(session, body)
    await _ensure_unique(session, GlossaryTerm, GlossaryTerm.slug, body.slug, None, "term")
    term = GlossaryTerm(**body.model_dump())
    session.add(term)
    await _commit_or_conflict(session, "term")
    await session.refresh(term)
    await _glossary_changed()
    return term


_TERM_TEXT = ("term_en", "definition_en", "example_en", "analogy_en", "key_takeaway_en")


async def update_term(session: AsyncSession, term_id: uuid.UUID, body: GlossaryIn) -> GlossaryTerm:
    term = await _get(session, GlossaryTerm, term_id)
    await _validate_glossary(session, body)
    await _ensure_unique(session, GlossaryTerm, GlossaryTerm.slug, body.slug, term_id, "term")
    text_changed = any(getattr(term, f) != getattr(body, f) for f in _TERM_TEXT)
    for key, value in body.model_dump().items():
        setattr(term, key, value)
    if text_changed:
        await session.execute(delete(GlossaryTranslation).where(GlossaryTranslation.term_id == term_id,
                                                                GlossaryTranslation.generated_by == "llm"))
        await session.execute(update(GlossaryTranslation).where(GlossaryTranslation.term_id == term_id)
                              .values(reviewed=False))
    await _commit_or_conflict(session, "term")
    await session.refresh(term)
    await _glossary_changed()
    return term


async def set_term_translation(session: AsyncSession, term_id: uuid.UUID, language: str,
                               body: GlossaryTranslationIn) -> dict:
    await _get(session, GlossaryTerm, term_id)
    stmt = insert(GlossaryTranslation).values(term_id=term_id, language=language, generated_by="human",
                                              reviewed=True, **body.model_dump())
    stmt = stmt.on_conflict_do_update(index_elements=["term_id", "language"], set_={
        **{k: getattr(stmt.excluded, k) for k in body.model_dump()}, "generated_by": "human", "reviewed": True})
    await session.execute(stmt)
    await session.commit()
    await _glossary_changed()  # local names are detector patterns
    return {"language": language, "generated_by": "human", "reviewed": True}


# --- Lessons & videos --------------------------------------------------------------

async def _validate_lesson(session: AsyncSession, body: LessonIn) -> None:
    if body.video_id and await session.get(Video, body.video_id) is None:
        raise _invalid([{"field": "video_id", "issue": "unknown video"}])


async def create_lesson(session: AsyncSession, body: LessonIn) -> Lesson:
    await _validate_lesson(session, body)
    await _ensure_unique(session, Lesson, Lesson.slug, body.slug, None, "lesson")
    lesson = Lesson(**body.model_dump())
    session.add(lesson)
    await _commit_or_conflict(session, "lesson")
    await session.refresh(lesson)
    return lesson


async def update_lesson(session: AsyncSession, lesson_id: uuid.UUID, body: LessonIn) -> Lesson:
    lesson = await _get(session, Lesson, lesson_id)
    await _validate_lesson(session, body)
    await _ensure_unique(session, Lesson, Lesson.slug, body.slug, lesson_id, "lesson")
    text_changed = lesson.title_en != body.title_en or lesson.body_md_en != body.body_md_en
    for key, value in body.model_dump().items():
        setattr(lesson, key, value)
    if text_changed:
        await session.execute(delete(LessonTranslation).where(LessonTranslation.lesson_id == lesson_id,
                                                              LessonTranslation.generated_by == "llm"))
        await session.execute(update(LessonTranslation).where(LessonTranslation.lesson_id == lesson_id)
                              .values(reviewed=False))
    await _commit_or_conflict(session, "lesson")
    await session.refresh(lesson)
    return lesson


async def register_video(session: AsyncSession, body: VideoIn) -> VideoUploadOut:
    video_id = uuid.uuid4()
    key = f"videos/{video_id}.mp4"  # spec §5.11
    session.add(Video(id=video_id, title=body.title, language=body.language, storage_key=key,
                      duration_sec=body.duration_sec))
    await session.commit()
    url = presigned_put(settings.S3_BUCKET_MEDIA, key, "video/mp4", UPLOAD_URL_TTL_SEC)
    return VideoUploadOut(id=video_id, upload_url=url, storage_key=key, expires_in_sec=UPLOAD_URL_TTL_SEC)


# --- Fraud patterns ----------------------------------------------------------------

async def _validate_pattern(session: AsyncSession, body: FraudPatternIn, pattern_id: uuid.UUID | None) -> None:
    errors = []
    if body.pattern_type == "regex":
        for i, p in enumerate(body.patterns):
            try:
                re.compile(p, re.IGNORECASE | re.UNICODE)
            except re.error as exc:
                errors.append({"field": f"patterns.{i}", "issue": f"invalid regex: {exc}"})
    if body.requires_codes:
        wanted = {c.lstrip("!") for c in body.requires_codes}
        known = set((await session.execute(select(FraudPattern.code).where(FraudPattern.code.in_(wanted)))).scalars())
        if wanted - known - {body.code}:
            errors.append({"field": "requires_codes", "issue": f"unknown codes {sorted(wanted - known)}"})
        if body.code in wanted:
            errors.append({"field": "requires_codes", "issue": "a rule can't require itself"})
    if errors:
        raise _invalid(errors)


async def list_patterns(session: AsyncSession) -> list[FraudPattern]:
    return list((await session.execute(select(FraudPattern).order_by(FraudPattern.code))).scalars())


async def create_pattern(session: AsyncSession, body: FraudPatternIn) -> FraudPattern:
    await _validate_pattern(session, body, None)
    await _ensure_unique(session, FraudPattern, FraudPattern.code, body.code, None, "fraud pattern")
    pattern = FraudPattern(**body.model_dump())
    session.add(pattern)
    await _commit_or_conflict(session, "fraud pattern")
    await session.refresh(pattern)
    await fraud_rules.invalidate_patterns()
    return pattern


async def update_pattern(session: AsyncSession, pattern_id: uuid.UUID, body: FraudPatternIn) -> FraudPattern:
    pattern = await _get(session, FraudPattern, pattern_id)
    await _validate_pattern(session, body, pattern_id)
    await _ensure_unique(session, FraudPattern, FraudPattern.code, body.code, pattern_id, "fraud pattern")
    for key, value in body.model_dump().items():
        setattr(pattern, key, value)
    await _commit_or_conflict(session, "fraud pattern")
    await session.refresh(pattern)
    await fraud_rules.invalidate_patterns()
    return pattern
