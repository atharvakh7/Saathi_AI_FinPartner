"""User profile, consents, devices, settings and account lifecycle (spec §7.4 /me/*)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.pii import mask_phone
from app.modules.auth.models import RefreshToken
from app.modules.users import events
from app.modules.users.models import Consent, DeviceToken, NotificationSettings, User, UserProfile
from app.modules.users.schemas import (
    ConfidenceIn,
    ConfidenceOut,
    ConsentOut,
    ConsentsIn,
    NotificationSettingsIn,
    OnboardingStep,
    ProfileIn,
    UserOut,
)

REQUIRED_CONSENTS = ("terms_privacy", "personalization")
# Current privacy notice. A user whose terms_privacy consent is for an older version is asked again
# (/me.needs = "consent"). 1.1: replies are written with a hosted LLM (Google Gemini).
PRIVACY_NOTICE_VERSION = "1.1"
# Fields S07 marks required; onboarding step "profile" is incomplete while any is null.
REQUIRED_PROFILE_FIELDS = (
    "full_name", "age_years", "state_code", "area_type", "occupation_type", "income_pattern",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def get_profile(session: AsyncSession, user: User) -> UserProfile | None:
    return await session.get(UserProfile, user.id)


async def ensure_profile(session: AsyncSession, user: User) -> UserProfile:
    profile = await get_profile(session, user)
    if profile is None:
        profile = UserProfile(user_id=user.id)
        session.add(profile)
        await session.flush()
    return profile


def to_user_out(user: User, profile: UserProfile | None) -> UserOut:
    full_name = (profile.full_name or "").strip() if profile else ""
    return UserOut(
        id=user.id,
        phone_masked=mask_phone(user.phone_e164),
        role=user.role,
        preferred_language=user.preferred_language,
        voice_reply_enabled=profile.voice_reply_enabled if profile else True,
        onboarding_completed_at=profile.onboarding_completed_at if profile else None,
        first_name=full_name.split()[0] if full_name else None,
    )


async def current_consents(session: AsyncSession, user_id) -> dict[str, Consent]:
    """Latest consent row per type (spec §6.1: latest row per type is current)."""
    rows = (
        await session.execute(
            select(Consent)
            .where(Consent.user_id == user_id)
            .order_by(Consent.consent_type, Consent.created_at.desc())
            .distinct(Consent.consent_type)
        )
    ).scalars()
    return {c.consent_type: c for c in rows}


async def next_onboarding_step(
    session: AsyncSession, user: User, profile: UserProfile | None
) -> OnboardingStep | None:
    """`needs` for GET /me (spec §7.4)."""
    consents = await current_consents(session, user.id)
    if not all(consents.get(t) and consents[t].granted for t in REQUIRED_CONSENTS):
        return "consent"
    if consents["terms_privacy"].version != PRIVACY_NOTICE_VERSION:
        return "consent"  # the notice changed since they agreed
    if profile is None or any(getattr(profile, f) is None for f in REQUIRED_PROFILE_FIELDS):
        return "profile"
    # Skipping the assessment stores [] so it is not asked again (ASSUMPTIONS C2).
    if profile.confidence_answers is None:
        return "confidence"
    if profile.onboarding_completed_at is None:
        return "goals"
    return None


# --- Profile -----------------------------------------------------------------------

async def update_profile(session: AsyncSession, user: User, body: ProfileIn) -> UserProfile:
    changes = body.model_dump(exclude_unset=True)
    not_nullable = [f for f in (*REQUIRED_PROFILE_FIELDS, "voice_reply_enabled") if f in changes and changes[f] is None]
    if not_nullable:
        raise AppError("VALIDATION_ERROR", details=[{"field": f, "issue": "is required"} for f in not_nullable])

    profile = await ensure_profile(session, user)
    for field, value in changes.items():
        setattr(profile, field, value)
    if profile.occupation_type == "student":
        profile.is_student = True  # spec §7.4: auto-set for students

    # Cross-field rules are checked on the merged result, not just the request body.
    errors = []
    lo, hi = profile.declared_monthly_income_min_inr, profile.declared_monthly_income_max_inr
    if lo is not None and hi is not None and hi < lo:
        errors.append({"field": "declared_monthly_income_max_inr", "issue": "must be at least the minimum income"})
    size, deps = profile.household_size, profile.dependents_count
    if size is not None and deps is not None and deps > size - 1:
        errors.append({"field": "dependents_count", "issue": "must be less than household size"})
    if errors:
        await session.rollback()
        raise AppError("VALIDATION_ERROR", details=errors)

    await session.commit()
    await events.profile_updated(user.id)
    return profile


def score_confidence(answers: list[int]) -> ConfidenceOut:
    """score_pct = round((sum − 5) / 20 × 100); low < 40, medium 40–69, high ≥ 70 (ASSUMPTIONS C1)."""
    if not answers:
        return ConfidenceOut(score_pct=None, level=None)
    pct = round((sum(answers) - 5) / 20 * 100)
    level = "low" if pct < 40 else "medium" if pct < 70 else "high"
    return ConfidenceOut(score_pct=pct, level=level)


async def submit_confidence(session: AsyncSession, user: User, body: ConfidenceIn) -> ConfidenceOut:
    result = score_confidence(body.answers)
    profile = await ensure_profile(session, user)
    profile.confidence_answers = body.answers  # [] = skipped, so /me.needs does not ask again
    profile.confidence_score_pct = result.score_pct
    profile.confidence_level = result.level
    await session.commit()
    return result


async def complete_onboarding(session: AsyncSession, user: User) -> UserProfile:
    profile = await ensure_profile(session, user)
    first_time = profile.onboarding_completed_at is None
    if first_time:
        profile.onboarding_completed_at = _now()
    await session.commit()
    if first_time:
        await events.onboarding_completed(user.id)
    return profile


# --- Consents ----------------------------------------------------------------------

def consents_out(current: dict[str, Consent]) -> list[ConsentOut]:
    return [
        ConsentOut(consent_type=c.consent_type, granted=c.granted, version=c.version, updated_at=c.created_at)
        for c in sorted(current.values(), key=lambda c: c.consent_type)
    ]


async def record_consents(session: AsyncSession, user: User, body: ConsentsIn) -> list[ConsentOut]:
    """Appends one audit row per submitted consent; the latest row per type is current."""
    current = await current_consents(session, user.id)
    submitted = {c.consent_type: c.granted for c in body.consents}

    first_submission = not all(t in current for t in REQUIRED_CONSENTS)
    if first_submission:
        missing = [t for t in REQUIRED_CONSENTS if submitted.get(t) is not True]
        if missing:
            raise AppError(
                "VALIDATION_ERROR",
                "Please agree to the required consents to continue.",
                details=[{"field": t, "issue": "must be granted"} for t in missing],
            )

    for consent_type, granted in submitted.items():
        session.add(Consent(user_id=user.id, consent_type=consent_type, version=body.version, granted=granted))

    # Withdrawing push consent also turns push off (DPDP withdrawal of consent).
    if submitted.get("push_notifications") is False:
        await session.execute(
            update(NotificationSettings).where(NotificationSettings.user_id == user.id).values(push_enabled=False)
        )
    await session.commit()
    return consents_out(await current_consents(session, user.id))


# --- Device tokens -----------------------------------------------------------------

async def register_device_token(session: AsyncSession, user: User, token: str, platform: str) -> uuid.UUID:
    """Upsert by token; a device that switches accounts moves to the new user."""
    stmt = insert(DeviceToken).values(user_id=user.id, expo_push_token=token, platform=platform)
    stmt = stmt.on_conflict_do_update(
        index_elements=["expo_push_token"],
        set_={"user_id": user.id, "platform": platform, "last_seen_at": _now()},
    ).returning(DeviceToken.id)
    token_id = (await session.execute(stmt)).scalar_one()
    await session.commit()
    return token_id


async def delete_device_token(session: AsyncSession, user: User, token_id: uuid.UUID) -> None:
    result = await session.execute(
        delete(DeviceToken).where(DeviceToken.id == token_id, DeviceToken.user_id == user.id)
    )
    if result.rowcount == 0:
        raise AppError("NOT_FOUND")
    await session.commit()


# --- Notification settings ---------------------------------------------------------

async def get_notification_settings(session: AsyncSession, user: User) -> NotificationSettings:
    ns = await session.get(NotificationSettings, user.id)
    if ns is None:
        ns = NotificationSettings(user_id=user.id)
        session.add(ns)
        await session.commit()
        await session.refresh(ns)
    return ns


async def update_notification_settings(
    session: AsyncSession, user: User, body: NotificationSettingsIn
) -> NotificationSettings:
    changes = body.model_dump(exclude_unset=True)
    nulls = [f for f, v in changes.items() if v is None]
    if nulls:
        raise AppError("VALIDATION_ERROR", details=[{"field": f, "issue": "cannot be null"} for f in nulls])
    ns = await get_notification_settings(session, user)
    for field, value in changes.items():
        setattr(ns, field, value)
    await session.commit()
    await session.refresh(ns)
    return ns


# --- Account deletion --------------------------------------------------------------

async def schedule_account_deletion(session: AsyncSession, user: User) -> None:
    """Soft-delete now; the maintenance.purge job hard-deletes after 30 days (spec §5.10)."""
    user.status = "deleted"
    user.deleted_at = _now()
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=_now())
    )
    await session.execute(delete(DeviceToken).where(DeviceToken.user_id == user.id))
    await session.commit()
