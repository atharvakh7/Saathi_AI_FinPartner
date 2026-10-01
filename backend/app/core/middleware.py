"""Pure-ASGI middleware: request context, security headers, body limits, global rate limits."""

import json
import logging
import time
import uuid

from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings
from app.core.errors import ERROR_CODES, error_body
from app.core.logging import reset_request_id, set_request_id
from app.core.rate_limit import hit
from app.core.security import decode_access_token

log = logging.getLogger("saathi.request")


def _header(scope: Scope, name: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key == name:
            return value.decode("latin-1")
    return None


async def _send_error(send: Send, code: str, extra_headers: dict[str, str] | None = None) -> None:
    status, message = ERROR_CODES[code]
    body = json.dumps(error_body(code, message), ensure_ascii=False).encode("utf-8")
    headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]
    for k, v in (extra_headers or {}).items():
        headers.append((k.lower().encode(), v.encode()))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


class RequestContextMiddleware:
    """Assigns request_id, logs each request, and adds security headers (spec §8.3)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = _header(scope, b"x-request-id")
        request_id = incoming if incoming and len(incoming) <= 64 else str(uuid.uuid4())
        token = set_request_id(request_id)
        authenticated = _header(scope, b"authorization") is not None
        started = time.perf_counter()
        status_holder = {"status": 500}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                headers.append((b"x-content-type-options", b"nosniff"))
                if authenticated:
                    headers.append((b"cache-control", b"no-store"))
                if settings.is_production:
                    headers.append((b"strict-transport-security", b"max-age=31536000; includeSubDomains"))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            log.info(
                "request",
                extra={
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                    "status": status_holder["status"],
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
            reset_request_id(token)


class BodyTooLarge(StarletteHTTPException):
    """HTTPException subclass so FastAPI's body parser re-raises it unchanged (→ 413 envelope)."""

    def __init__(self) -> None:
        super().__init__(status_code=413)


class BodySizeLimitMiddleware:
    """64 KB for JSON, 6 MB for multipart uploads (spec §8.3)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_type = (_header(scope, b"content-type") or "").lower()
        limit = (
            settings.MAX_UPLOAD_BODY_BYTES
            if content_type.startswith("multipart/form-data")
            else settings.MAX_JSON_BODY_BYTES
        )

        declared = _header(scope, b"content-length")
        if declared and declared.isdigit() and int(declared) > limit:
            await _send_error(send, "PAYLOAD_TOO_LARGE")
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise BodyTooLarge()
            return message

        await self.app(scope, limited_receive, send)


class RateLimitMiddleware:
    """Global limits: RATE_LIMIT_IP_PER_MIN per IP and RATE_LIMIT_USER_PER_MIN per user.

    Also exposes the token's user id on request.state.user_id (without raising on a bad
    token — authentication itself is enforced by route dependencies).
    """

    EXEMPT_PATHS = {f"{settings.API_PREFIX}/health"}

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") in self.EXEMPT_PATHS:
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        ip = client[0] if client else "unknown"
        retry_after = await hit(f"global:ip:{ip}", settings.RATE_LIMIT_IP_PER_MIN, 60)

        user_id = None
        auth = _header(scope, b"authorization") or ""
        if retry_after is None and auth.lower().startswith("bearer "):
            try:
                user_id = str(decode_access_token(auth[7:].strip()).user_id)
            except Exception:
                user_id = None
            if user_id:
                retry_after = await hit(f"global:u:{user_id}", settings.RATE_LIMIT_USER_PER_MIN, 60)

        if retry_after is not None:
            await _send_error(send, "RATE_LIMITED", {"Retry-After": str(retry_after)})
            return

        scope.setdefault("state", {})["user_id"] = user_id
        await self.app(scope, receive, send)
