"""JWT access tokens, refresh/OTP hashing, and auth dependencies (spec §8.1)."""

import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.errors import AppError
from app.modules.users.models import User

JWT_ALGORITHM = "HS256"


@dataclass(frozen=True)
class TokenClaims:
    user_id: uuid.UUID
    role: str
    jti: str
    exp: datetime


def create_access_token(user_id: uuid.UUID, role: str) -> tuple[str, int]:
    """Returns (jwt, expires_in_seconds)."""
    now = datetime.now(timezone.utc)
    ttl = settings.JWT_ACCESS_TTL_SEC
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM), ttl


def decode_access_token(token: str) -> TokenClaims:
    """Raises AppError TOKEN_EXPIRED or UNAUTHENTICATED."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp", "iat", "jti"]},
        )
        return TokenClaims(
            user_id=uuid.UUID(payload["sub"]),
            role=payload.get("role", "user"),
            jti=payload["jti"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
    except jwt.ExpiredSignatureError as exc:
        raise AppError("TOKEN_EXPIRED") from exc
    except (jwt.InvalidTokenError, ValueError, KeyError) as exc:
        raise AppError("UNAUTHENTICATED") from exc


def bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def get_token_claims(request: Request) -> TokenClaims:
    """FastAPI dependency: validated claims from the Authorization header."""
    token = bearer_token(request)
    if token is None:
        raise AppError("UNAUTHENTICATED")
    return decode_access_token(token)


async def get_current_user(
    claims: TokenClaims = Depends(get_token_claims),
    session: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency: the active User for the bearer token.

    Every query in route handlers must filter by this user's id (spec §8.1).
    """
    user = await session.get(User, claims.user_id)
    if user is None or user.status != "active":
        raise AppError("UNAUTHENTICATED")
    return user


def require_role(role: str):
    """Dependency factory, e.g. `Depends(require_role("admin"))` (403 FORBIDDEN otherwise)."""

    async def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise AppError("FORBIDDEN")
        return user

    return _dependency


# --- Refresh tokens: 64-byte URL-safe random, stored only as SHA-256 hash ---

def new_refresh_token() -> tuple[str, str]:
    """Returns (plain_token, sha256_hex)."""
    plain = secrets.token_urlsafe(64)
    return plain, sha256_hex(plain)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


# --- OTP codes: 6 digits from secrets, stored as HMAC-SHA256 ---

def new_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def otp_hash(phone_e164: str, code: str) -> str:
    msg = f"{phone_e164}:{code}".encode("utf-8")
    return hmac.new(settings.OTP_HMAC_KEY.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def otp_matches(phone_e164: str, code: str, stored_hash: str) -> bool:
    return hmac.compare_digest(otp_hash(phone_e164, code), stored_hash)
