"""Error envelope and codes (spec §7.1).

Every error response has the shape:
    {"error": {"code": str, "message": str, "details": list|dict|null, "request_id": str}}
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_request_id

log = logging.getLogger(__name__)

# code -> (HTTP status, default English message)
ERROR_CODES: dict[str, tuple[int, str]] = {
    "VALIDATION_ERROR": (422, "Some of the information is not valid."),
    "UNAUTHENTICATED": (401, "Please log in again."),
    "TOKEN_EXPIRED": (401, "Your session has expired."),
    "FORBIDDEN": (403, "You do not have permission to do this."),
    "NOT_FOUND": (404, "We couldn't find that."),
    "CONFLICT": (409, "This conflicts with existing data."),
    "ONBOARDING_INCOMPLETE": (409, "Please finish setting up your profile first."),
    "OTP_INVALID": (400, "Wrong code."),
    "OTP_EXPIRED": (400, "This code has expired. Please request a new one."),
    "OTP_LOCKED": (429, "Too many wrong attempts. Please try again later."),
    "RATE_LIMITED": (429, "Too many attempts. Try again later."),
    "PAYLOAD_TOO_LARGE": (413, "The file or message is too large."),
    "UNSUPPORTED_MEDIA_TYPE": (415, "This file type is not supported."),
    "TRANSCRIPTION_FAILED": (422, "I couldn't hear that. Please try again."),
    "OCR_NO_TEXT": (422, "I couldn't read any text in this image. Try a clearer screenshot."),
    "UPSTREAM_AI_UNAVAILABLE": (503, "I'm having trouble right now. Please try again."),
    "INTERNAL": (500, "Something went wrong. Please try again."),
}

# Fallback mapping for framework-raised HTTP errors.
_STATUS_TO_CODE = {
    400: "VALIDATION_ERROR",
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "NOT_FOUND",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    503: "UPSTREAM_AI_UNAVAILABLE",
}


class AppError(Exception):
    """Raise anywhere in request handling to return a spec-shaped error."""

    def __init__(
        self,
        code: str,
        message: str | None = None,
        details: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        if code not in ERROR_CODES:
            raise ValueError(f"Unknown error code {code}")
        self.code = code
        self.status_code, default_message = ERROR_CODES[code]
        self.message = message or default_message
        self.details = details
        self.headers = headers
        super().__init__(f"{code}: {self.message}")


def error_body(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": get_request_id(),
        }
    }


def error_response(
    code: str,
    message: str | None = None,
    details: Any = None,
    headers: dict[str, str] | None = None,
    status_code: int | None = None,
) -> JSONResponse:
    status, default_message = ERROR_CODES[code]
    return JSONResponse(
        status_code=status_code or status,
        content=error_body(code, message or default_message, details),
        headers=headers,
    )


def _validation_details(exc: RequestValidationError) -> list[dict[str, str]]:
    details = []
    for err in exc.errors():
        # loc is e.g. ("body", "amount_inr") or ("query", "month"); drop the location prefix.
        loc = [str(p) for p in err.get("loc", ()) if p not in ("body", "query", "path", "header", "form")]
        details.append({"field": ".".join(loc) or "body", "issue": err.get("msg", "invalid")})
    return details


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return error_response(exc.code, exc.message, exc.details, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response("VALIDATION_ERROR", details=_validation_details(exc))

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _STATUS_TO_CODE.get(exc.status_code, "INTERNAL")
        return error_response(code, headers=getattr(exc, "headers", None), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error", exc_info=exc)
        return error_response("INTERNAL")
