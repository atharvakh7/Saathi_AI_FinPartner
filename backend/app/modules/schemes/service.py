"""Scheme Scout: catalog, matching, questions, detail and tracking (spec §5.6, §7.4 /schemes/*).

A scheme applies to a user when it is active and central, or a state scheme of the user's state.
Matches are stored per user in user_scheme_matches and recomputed on profile changes (event
handler below; Celery `schemes.recompute` in step 17), on POST /schemes/eligibility/check, and
when stale (older than 24 h, or the set of applicable schemes changed).
"""

import logging
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from pydantic import ValidationError
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIUnavailable
from app.core import events
from app.core.db import SessionLocal
from app.core.errors import AppError
from app.core.pagination import after_cursor, decode_cursor, encode_cursor
from app.modules.schemes import translate
from app.modules.schemes.eligibility import (
    UNDISCLOSED,
    RuleIn,
    evaluate_scheme,
    failed_rules,
    missing_fields,
    profile_values,
)
from app.modules.schemes.field_registry import FIELDS
from app.modules.schemes.models import (
    Scheme,
    SchemeCategory,
    SchemeDocument,
    SchemeEligibilityRule,
    SchemeStep,
    SchemeTranslation,
    UserSchemeMatch,
    UserSchemeTracking,
)
from app.modules.schemes.schemas import (
    CategoryOut,
    DocumentOut,
    FailedReason,
    MatchesOut,
    MatchItem,
    MatchOut,
    QuestionOut,
    QuestionsOut,
    RuleResultOut,
    SchemeDetail,
    SchemeInfo,
    SchemePage,
    SchemeSummary,
    StepOut,
)
from app.modules.users import service as users_service
from app.modules.users.models import User, UserProfile
from app.modules.users.schemas import ProfileIn

log = logging.getLogger(__name__)

MATCHES_MAX_AGE = timedelta(hours=24)
MAX_QUESTIONS = 12
STATUS_ORDER = {"eligible": 0, "possibly_eligible": 1, "not_eligible": 2}
QUESTION_TYPES = {"bool": "boolean", "int": "number", "enum": "enum", "str": "enum"}
FIELD_ORDER = {name: i for i, name in enumerate(FIELDS)}

# Spec A9: shown with every scheme.
DISCLAIMERS = {
    "en": "Please confirm details on the official website before applying.",
    "hi": "आवेदन करने से पहले कृपया आधिकारिक वेबसाइट पर जानकारी की पुष्टि करें।",
    "mr": "अर्ज करण्यापूर्वी कृपया अधिकृत वेबसाइटवर माहितीची खात्री करून घ्या.",
    "ta": "விண்ணப்பிக்கும் முன் அதிகாரப்பூர்வ இணையதளத்தில் விவரங்களை உறுதிப்படுத்திக் கொள்ளவும்.",
}


def _applicable(state_code: str | None):
    scope = Scheme.level == "central"
    if state_code:
        scope = or_(scope, Scheme.state_code == state_code)
    return and_(Scheme.is_active, scope)


async def _profile(session: AsyncSession, user_id: uuid.UUID) -> UserProfile | None:
    return await session.get(UserProfile, user_id)


async def _rules_by_scheme(session: AsyncSession, scheme_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[RuleIn]]:
    rows = (
        await session.execute(
            select(SchemeEligibilityRule)
            .where(SchemeEligibilityRule.scheme_id.in_(scheme_ids))
            .order_by(SchemeEligibilityRule.is_mandatory.desc(), SchemeEligibilityRule.rule_key)
        )
    ).scalars()
    out: dict[uuid.UUID, list[RuleIn]] = {sid: [] for sid in scheme_ids}
    for r in rows:
        out[r.scheme_id].append(RuleIn(r.rule_key, r.field, r.operator, r.value, r.is_mandatory, r.explanation_en))
    return out


async def _contents(session: AsyncSession, scheme_ids, language: str) -> dict[uuid.UUID, SchemeTranslation]:
    if language == "en" or not scheme_ids:
        return {}
    rows = (
        await session.execute(
            select(SchemeTranslation)
            .where(SchemeTranslation.scheme_id.in_(scheme_ids), SchemeTranslation.language == language)
        )
    ).scalars()
    return {t.scheme_id: t for t in rows}


def _summary(scheme: Scheme, tr: SchemeTranslation | None, status: str | None) -> SchemeSummary:
    content = tr.content if tr else {}
    return SchemeSummary(
        id=scheme.id, slug=scheme.slug, name=content.get("name") or scheme.name_en,
        level=scheme.level, state_code=scheme.state_code, category_slug=scheme.category_slug,
        benefit_summary=content.get("benefit_summary") or scheme.benefit_summary_en, match_status=status,
    )


def _explanation(rule: dict, tr: SchemeTranslation | None) -> str:
    if tr is not None:
        local = (tr.content.get("rule_explanations") or {}).get(rule["rule_key"])
        if local:
            return local
    return rule["explanation"]


# --- Matching ----------------------------------------------------------------------

async def recompute(session: AsyncSession, user_id: uuid.UUID) -> dict:
    """Evaluate every applicable scheme for the user and store the results.

    Returns counts per status and `newly_eligible` (scheme ids that just became eligible; used by
    insight I09 in step 17).
    """
    values = profile_values(await _profile(session, user_id))
    schemes = list((await session.execute(select(Scheme.id).where(_applicable(values["state_code"])))).scalars())
    rules = await _rules_by_scheme(session, schemes)
    previous = dict(
        (await session.execute(
            select(UserSchemeMatch.scheme_id, UserSchemeMatch.status).where(UserSchemeMatch.user_id == user_id)
        )).all()
    )
    now = datetime.now(timezone.utc)
    rows = []
    for sid in schemes:
        status, results = evaluate_scheme(rules[sid], values)
        rows.append({"user_id": user_id, "scheme_id": sid, "status": status, "rule_results": results,
                     "computed_at": now})
    if rows:
        stmt = insert(UserSchemeMatch).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id", "scheme_id"],
            set_={"status": stmt.excluded.status, "rule_results": stmt.excluded.rule_results,
                  "computed_at": stmt.excluded.computed_at},
        )
        await session.execute(stmt)
    # Schemes no longer applicable (state changed, scheme deactivated) lose their stored match.
    await session.execute(
        delete(UserSchemeMatch).where(UserSchemeMatch.user_id == user_id, UserSchemeMatch.scheme_id.not_in(schemes))
    )
    await session.commit()
    counts = Counter(r["status"] for r in rows)
    return {
        "eligible": counts["eligible"],
        "possibly_eligible": counts["possibly_eligible"],
        "not_eligible": counts["not_eligible"],
        "newly_eligible": [r["scheme_id"] for r in rows
                           if r["status"] == "eligible" and previous.get(r["scheme_id"]) != "eligible"],
    }


@events.on(events.PROFILE_UPDATED)
@events.on(events.ONBOARDING_COMPLETED)
async def recompute_after_change(user_id: uuid.UUID) -> None:
    async with SessionLocal() as session:
        result = await recompute(session, user_id)
    await announce_new_matches(user_id, result["newly_eligible"])


async def announce_new_matches(user_id: uuid.UUID, scheme_ids: list) -> None:
    """Insight I09 "You may now qualify for {n} new schemes" (spec §5.9)."""
    if not scheme_ids:
        return
    from app.jobs import dispatch  # queued: phrasing it in the user's language takes an LLM call

    await dispatch.enqueue("insights.scheme_news", user_id, ",".join(str(i) for i in scheme_ids))


async def ensure_matches(session: AsyncSession, user: User) -> None:
    """Recompute when nothing is stored, the oldest result is over 24 h old, or the scheme set changed."""
    profile = await _profile(session, user.id)
    applicable = (
        await session.execute(select(func.count(Scheme.id)).where(_applicable(profile.state_code if profile else None)))
    ).scalar_one()
    stored, oldest = (
        await session.execute(
            select(func.count(UserSchemeMatch.id), func.min(UserSchemeMatch.computed_at))
            .join(Scheme, Scheme.id == UserSchemeMatch.scheme_id)
            .where(UserSchemeMatch.user_id == user.id, Scheme.is_active)
        )
    ).one()
    if stored != applicable or oldest is None or datetime.now(timezone.utc) - oldest > MATCHES_MAX_AGE:
        await recompute(session, user.id)


async def matches(session: AsyncSession, user: User, language: str) -> MatchesOut:
    await ensure_matches(session, user)
    rows = (
        await session.execute(
            select(Scheme, UserSchemeMatch)
            .join(UserSchemeMatch, UserSchemeMatch.scheme_id == Scheme.id)
            .where(UserSchemeMatch.user_id == user.id, Scheme.is_active)
        )
    ).all()
    trs = await _contents(session, [s.id for s, _ in rows], language)
    items = []
    for scheme, match in rows:
        tr = trs.get(scheme.id)
        items.append(MatchItem(
            scheme=_summary(scheme, tr, match.status),
            status=match.status,
            missing_fields=missing_fields(match.rule_results) if match.status == "possibly_eligible" else [],
            reasons=[FailedReason(rule_key=r["rule_key"], field=r["field"], explanation=_explanation(r, tr))
                     for r in failed_rules(match.rule_results)],
        ))
    items.sort(key=lambda i: (STATUS_ORDER[i.status], len(i.missing_fields), i.scheme.name.lower()))
    counts = Counter(i.status for i in items)
    return MatchesOut(
        eligible_count=counts["eligible"],
        possibly_eligible_count=counts["possibly_eligible"],
        total=counts["eligible"] + counts["possibly_eligible"],
        items=items,
    )


async def top_matches(session: AsyncSession, user: User, language: str, limit: int = 5) -> list[SchemeSummary]:
    """For the chat `scheme_query` intent (spec §5.3): best eligible / possibly eligible schemes."""
    result = await matches(session, user, language)
    return [i.scheme for i in result.items if i.status != "not_eligible"][:limit]


# --- Questions & answers -----------------------------------------------------------

async def questions(session: AsyncSession, user: User) -> QuestionsOut:
    """Unknown fields that could still decide a scheme, most schemes affected first (max 12).

    Only possibly-eligible schemes count: an eligible scheme has nothing unknown, and asking about a
    scheme that already fails another rule cannot change its result (ASSUMPTIONS step 13).
    """
    await ensure_matches(session, user)
    rows = (
        await session.execute(
            select(UserSchemeMatch.rule_results)
            .join(Scheme, Scheme.id == UserSchemeMatch.scheme_id)
            .where(UserSchemeMatch.user_id == user.id, UserSchemeMatch.status == "possibly_eligible", Scheme.is_active)
        )
    ).scalars()
    counts: Counter[str] = Counter()
    for rule_results in rows:
        counts.update(missing_fields(rule_results))
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], FIELD_ORDER[kv[0]]))[:MAX_QUESTIONS]
    out = []
    for field, n in ranked:
        spec = FIELDS[field]
        options = [o for o in spec.options if o != UNDISCLOSED] if spec.options else None
        out.append(QuestionOut(field=field, type=QUESTION_TYPES[spec.type], options=options, affects_count=n))
    return QuestionsOut(questions=out)


def _parse_answers(answers: dict) -> dict:
    """Type-check answers against the field registry; nulls ("Not sure") are dropped."""
    errors, clean = [], {}
    for field, value in answers.items():
        spec = FIELDS.get(field)
        if spec is None:
            errors.append({"field": f"answers.{field}", "issue": "unknown field"})
            continue
        if value is None:
            continue
        if spec.type == "bool":
            ok = isinstance(value, bool)
        elif spec.type == "int":
            ok = isinstance(value, int) and not isinstance(value, bool)
        else:
            ok = isinstance(value, str) and value in spec.options
        if not ok:
            expected = {"bool": "true or false", "int": "a whole number"}.get(spec.type) or f"one of {list(spec.options)}"
            errors.append({"field": f"answers.{field}", "issue": f"must be {expected}"})
            continue
        clean[field] = value
    if errors:
        raise AppError("VALIDATION_ERROR", details=errors)
    return clean


async def check(session: AsyncSession, user: User, answers: dict, language: str) -> MatchesOut:
    clean = _parse_answers(answers)
    if clean:
        try:
            body = ProfileIn.model_validate(clean)  # same ranges as PUT /me/profile (e.g. age 18–100)
        except ValidationError as exc:
            raise AppError("VALIDATION_ERROR", details=[
                {"field": "answers." + ".".join(str(p) for p in e["loc"]), "issue": e["msg"]} for e in exc.errors()
            ]) from exc
        # Persists into the profile and emits profile_updated (planner regenerate + our recompute).
        await users_service.update_profile(session, user, body)
    await recompute(session, user.id)  # explicit, so the response never depends on a handler having run
    return await matches(session, user, language)


# --- Catalog -----------------------------------------------------------------------

async def categories(session: AsyncSession, user: User) -> list[CategoryOut]:
    profile = await _profile(session, user.id)
    rows = (
        await session.execute(
            select(SchemeCategory, func.count(Scheme.id))
            .outerjoin(Scheme, and_(Scheme.category_slug == SchemeCategory.slug,
                                    _applicable(profile.state_code if profile else None)))
            .group_by(SchemeCategory.slug)
            .order_by(SchemeCategory.sort_order)
        )
    ).all()
    return [CategoryOut(slug=c.slug, name=c.name_en, icon=c.icon, count=n) for c, n in rows]


async def list_schemes(
    session: AsyncSession, user: User, *, category: str | None, q: str | None, status: str | None,
    limit: int, cursor: str | None, language: str,
) -> SchemePage:
    await ensure_matches(session, user)
    profile = await _profile(session, user.id)
    name_key = func.lower(Scheme.name_en).collate("C")  # byte order: same in SQL, cursors and tests
    stmt = (
        select(Scheme, UserSchemeMatch.status, SchemeTranslation)
        .outerjoin(UserSchemeMatch, and_(UserSchemeMatch.scheme_id == Scheme.id, UserSchemeMatch.user_id == user.id))
        .outerjoin(SchemeTranslation, and_(SchemeTranslation.scheme_id == Scheme.id,
                                           SchemeTranslation.language == language))
        .where(_applicable(profile.state_code if profile else None))
    )
    if category:
        stmt = stmt.where(Scheme.category_slug == category)
    if status:
        stmt = stmt.where(UserSchemeMatch.status == status)
    q = (q or "").strip()
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Scheme.name_en.ilike(like), Scheme.slug.ilike(like),
                              SchemeTranslation.content["name"].astext.ilike(like)))
    if cursor:
        stmt = stmt.where(after_cursor([name_key, Scheme.id], decode_cursor(cursor, [str, uuid.UUID]),
                                       descending=False))
    rows = (await session.execute(stmt.order_by(name_key, Scheme.id).limit(limit + 1))).all()
    page = rows[:limit]
    next_cursor = encode_cursor([page[-1][0].name_en.lower(), page[-1][0].id]) if len(rows) > limit else None
    return SchemePage(items=[_summary(s, tr, st) for s, st, tr in page], next_cursor=next_cursor)


async def _active_scheme(session: AsyncSession, scheme_id: uuid.UUID) -> Scheme:
    scheme = await session.get(Scheme, scheme_id)
    if scheme is None or not scheme.is_active:
        raise AppError("NOT_FOUND")
    return scheme


async def detail(session: AsyncSession, user: User, scheme_id: uuid.UUID, language: str) -> SchemeDetail:
    scheme = await _active_scheme(session, scheme_id)
    tr = None
    if language != "en":
        try:
            tr = await translate.translate_scheme(session, scheme, language)
        except AIUnavailable as exc:  # spec §7.4: English content, translation_source null, still 200
            log.warning("scheme translation unavailable", extra={"slug": scheme.slug, "error": str(exc)})
    content = tr.content if tr else {}

    steps = list((await session.execute(
        select(SchemeStep).where(SchemeStep.scheme_id == scheme.id).order_by(SchemeStep.step_no)
    )).scalars())
    docs = list((await session.execute(
        select(SchemeDocument).where(SchemeDocument.scheme_id == scheme.id)
        .order_by(SchemeDocument.sort_order, SchemeDocument.document_name_en)
    )).scalars())
    local_steps = content.get("steps") or []
    if len(local_steps) != len(steps):  # English content changed after translating
        local_steps = [{"title": s.title_en, "description": s.description_en} for s in steps]
    local_docs = content.get("documents") or []
    if len(local_docs) != len(docs):
        local_docs = [d.document_name_en for d in docs]

    # Evaluated live, so the result reflects the latest profile even before a recompute.
    rules = (await _rules_by_scheme(session, [scheme.id]))[scheme.id]
    status, results = evaluate_scheme(rules, profile_values(await _profile(session, user.id)))
    tracking = (
        await session.execute(
            select(UserSchemeTracking.status)
            .where(UserSchemeTracking.user_id == user.id, UserSchemeTracking.scheme_id == scheme.id)
        )
    ).scalar_one_or_none()

    shown = language if tr else "en"
    return SchemeDetail(
        scheme=SchemeInfo(
            id=scheme.id, slug=scheme.slug, name=content.get("name") or scheme.name_en,
            level=scheme.level, state_code=scheme.state_code, category_slug=scheme.category_slug,
            ministry_or_dept=scheme.ministry_or_dept, benefit_type=scheme.benefit_type,
            benefit_summary=content.get("benefit_summary") or scheme.benefit_summary_en,
            description=content.get("description") or scheme.description_en,
            application_mode=scheme.application_mode_en, official_url=scheme.official_url,
            last_verified_on=scheme.last_verified_on, deadline_on=scheme.deadline_on,
            translation_source=tr.generated_by if tr else None,
        ),
        match=MatchOut(status=status, rules=[
            RuleResultOut(rule_key=r["rule_key"], field=r["field"], result=r["result"],
                          explanation=_explanation(r, tr)) for r in results
        ]),
        steps=[StepOut(step_no=s.step_no, title=ls["title"], description=ls["description"])
               for s, ls in zip(steps, local_steps)],
        documents=[DocumentOut(name=name, is_mandatory=d.is_mandatory) for d, name in zip(docs, local_docs)],
        tracking_status=tracking,
        language=shown,
        disclaimer=DISCLAIMERS[shown],
    )


# --- Tracking ----------------------------------------------------------------------

async def set_tracking(session: AsyncSession, user: User, scheme_id: uuid.UUID, status: str | None) -> str | None:
    await _active_scheme(session, scheme_id)
    if status is None:
        await session.execute(
            delete(UserSchemeTracking)
            .where(UserSchemeTracking.user_id == user.id, UserSchemeTracking.scheme_id == scheme_id)
        )
    else:
        stmt = insert(UserSchemeTracking).values(user_id=user.id, scheme_id=scheme_id, status=status)
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id", "scheme_id"], set_={"status": status, "updated_at": func.now()}
        )
        await session.execute(stmt)
    await session.commit()
    return status
