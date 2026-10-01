"""Phone OTP login and token lifecycle (spec §7.4 /auth/*, §8.1).

- OTP: 6 digits, 5-minute validity, single use, HMAC-hashed, 5 wrong attempts -> 15-minute
  lock per phone. Request limits: 3/phone/15 min, 10/phone/day, 20/IP/hour.
- Access token: 15-minute JWT. Refresh token: opaque, stored as SHA-256, 30 days,
  rotated on every use; presenting a revoked token revokes all of the user's tokens.
"""

import ipaddress
import logging
import uuid
from datetime import datetime, timedelta, timezone

from redis.exceptions import RedisError
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError
from app.core.pii import mask_phone
from app.core.rate_limit import hit, rate_limited_error
from app.core.redis import redis_client
from app.core.security import create_access_token, new_otp_code, new_refresh_token, otp_hash, otp_matches, sha256_hex
from app.modules.auth.models import OtpRequest, RefreshToken
from app.modules.auth.otp_sender import send_otp
from app.modules.learn.models import UserLearningStats
from app.modules.users.models import NotificationSettings, User, UserProfile

log = logging.getLogger(__name__)

OTP_TTL_SEC = 300
OTP_RESEND_AFTER_SEC = 30
OTP_MAX_ATTEMPTS = 5
OTP_LOCK_SEC = 15 * 60

# (key suffix, limit, window seconds)
_PHONE_LIMITS = (("15m", 3, 15 * 60), ("day", 10, 24 * 3600))
_IP_LIMIT = (20, 3600)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _lock_key(phone: str) -> str:
    return f"otp_lock:{phone}"


async def _raise_if_locked(phone: str) -> None:
    try:
        ttl = await redis_client.ttl(_lock_key(phone))
    except RedisError as exc:  # fail open like the rate limiter; DB attempts still cap guesses
        log.warning("otp lock check unavailable", extra={"error": str(exc)})
        return
    if ttl and ttl > 0:
        raise AppError(
            "OTP_LOCKED",
            details={"minutes_remaining": -(-ttl // 60), "retry_after_sec": ttl},
            headers={"Retry-After": str(ttl)},
        )


def _valid_ip(value: str | None) -> str | None:
    try:
        return str(ipaddress.ip_address(value)) if value else None
    except ValueError:
        return None


# --- OTP ---------------------------------------------------------------------------

async def request_otp(session: AsyncSession, phone: str, client_ip: str | None) -> OtpRequest:
    await _raise_if_locked(phone)

    # Resend spacing, then per-phone and per-IP windows.
    last = (
        await session.execute(
            select(OtpRequest.created_at)
            .where(OtpRequest.phone_e164 == phone)
            .order_by(OtpRequest.created_at.desc())
            .limit(1)
        )
    ).scalar()
    if last is not None:
        wait = OTP_RESEND_AFTER_SEC - int((_now() - last).total_seconds())
        if wait > 0:
            raise rate_limited_error(wait)
    for suffix, limit, window in _PHONE_LIMITS:
        retry = await hit(f"otp:phone:{suffix}:{phone}", limit, window)
        if retry is not None:
            raise rate_limited_error(retry)
    if client_ip:
        retry = await hit(f"otp:ip:{client_ip}", *_IP_LIMIT)
        if retry is not None:
            raise rate_limited_error(retry)

    code = new_otp_code()
    otp = OtpRequest(
        phone_e164=phone,
        code_hash=otp_hash(phone, code),
        expires_at=_now() + timedelta(seconds=OTP_TTL_SEC),
        request_ip=_valid_ip(client_ip),
    )
    session.add(otp)
    await session.flush()
    await send_otp(phone, code, OTP_TTL_SEC)  # raises before commit if delivery fails
    await session.commit()
    return otp


async def _create_user(session: AsyncSession, phone: str, role: str) -> User:
    user = User(phone_e164=phone, role=role)
    session.add(user)
    await session.flush()
    session.add_all([
        UserProfile(user_id=user.id),
        NotificationSettings(user_id=user.id),
        UserLearningStats(user_id=user.id),
    ])
    await session.flush()
    return user


async def verify_otp(
    session: AsyncSession, phone: str, code: str, device_id: str | None
) -> tuple[User, bool, str, str, int]:
    """Returns (user, is_new_user, access_token, refresh_token, expires_in)."""
    await _raise_if_locked(phone)

    otp = (
        await session.execute(
            select(OtpRequest)
            .where(OtpRequest.phone_e164 == phone, OtpRequest.consumed_at.is_(None))
            .order_by(OtpRequest.created_at.desc())
            .limit(1)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if otp is None or otp.expires_at <= _now():
        raise AppError("OTP_EXPIRED")

    if not otp_matches(phone, code, otp.code_hash):
        otp.attempts += 1
        attempts_left = OTP_MAX_ATTEMPTS - otp.attempts
        if attempts_left <= 0:
            otp.consumed_at = _now()  # burn the code
            await session.commit()
            try:
                await redis_client.set(_lock_key(phone), "1", ex=OTP_LOCK_SEC)
            except RedisError as exc:
                log.warning("could not set otp lock", extra={"error": str(exc)})
            log.warning("otp locked after failed attempts", extra={"phone": mask_phone(phone)})
            raise AppError(
                "OTP_LOCKED",
                details={"minutes_remaining": OTP_LOCK_SEC // 60, "retry_after_sec": OTP_LOCK_SEC},
                headers={"Retry-After": str(OTP_LOCK_SEC)},
            )
        await session.commit()
        raise AppError("OTP_INVALID", details={"attempts_left": attempts_left})

    otp.consumed_at = _now()
    is_admin_phone = bool(settings.ADMIN_PHONE_E164) and phone == settings.ADMIN_PHONE_E164

    user = (await session.execute(select(User).where(User.phone_e164 == phone))).scalar_one_or_none()
    if user is not None and user.status == "deleted":
        # Account was scheduled for erasure: finish the erasure now and start fresh.
        await session.execute(delete(User).where(User.id == user.id))
        await session.flush()
        user = None

    is_new_user = user is None
    if user is None:
        user = await _create_user(session, phone, "admin" if is_admin_phone else "user")
    elif is_admin_phone and user.role != "admin":
        user.role = "admin"
    user.last_login_at = _now()

    access, refresh, expires_in, _ = await _issue_tokens(session, user, device_id)
    await session.commit()
    return user, is_new_user, access, refresh, expires_in


# --- Tokens ------------------------------------------------------------------------

async def _issue_tokens(
    session: AsyncSession, user: User, device_id: str | None
) -> tuple[str, str, int, uuid.UUID]:
    """Returns (access_token, refresh_token, expires_in, refresh_row_id)."""
    access, expires_in = create_access_token(user.id, user.role)
    plain, token_hash = new_refresh_token()
    row_id = uuid.uuid4()
    session.add(RefreshToken(
        id=row_id,
        user_id=user.id,
        token_hash=token_hash,
        device_id=device_id,
        expires_at=_now() + timedelta(days=settings.JWT_REFRESH_TTL_DAYS),
    ))
    await session.flush()
    return access, plain, expires_in, row_id


async def revoke_all_tokens(session: AsyncSession, user_id: uuid.UUID) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=_now())
    )


async def refresh_tokens(session: AsyncSession, refresh_token: str) -> tuple[str, str, int]:
    row = (
        await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == sha256_hex(refresh_token)).with_for_update()
        )
    ).scalar_one_or_none()
    if row is None:
        raise AppError("UNAUTHENTICATED")

    if row.revoked_at is not None:
        # Reuse of a rotated/revoked token: assume theft and end every session.
        await revoke_all_tokens(session, row.user_id)
        await session.commit()
        log.warning("refresh token reuse detected; all sessions revoked", extra={"user_id": str(row.user_id)})
        raise AppError("UNAUTHENTICATED")
    if row.expires_at <= _now():
        raise AppError("UNAUTHENTICATED")

    user = await session.get(User, row.user_id)
    if user is None or user.status != "active":
        raise AppError("UNAUTHENTICATED")

    access, plain, expires_in, new_row_id = await _issue_tokens(session, user, row.device_id)
    row.revoked_at = _now()
    row.replaced_by = new_row_id
    await session.commit()
    return access, plain, expires_in


async def logout(session: AsyncSession, user: User, refresh_token: str) -> None:
    """Revokes the given refresh token if it belongs to the user. Idempotent."""
    await session.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == sha256_hex(refresh_token),
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=_now())
    )
    await session.commit()
