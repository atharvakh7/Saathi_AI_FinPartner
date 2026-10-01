"""Structured JSON logging with request_id and PII redaction (spec §8.2, §8.4)."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

from app.core.pii import redact_pii

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return _request_id.get()


def set_request_id(value: str | None):
    return _request_id.set(value)


def reset_request_id(token) -> None:
    _request_id.reset(token)


_STD_ATTRS = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": redact_pii(record.getMessage()),
        }
        rid = get_request_id()
        if rid:
            payload["request_id"] = rid
        # Extra fields passed via logger.info("...", extra={...})
        for key, value in record.__dict__.items():
            if key not in _STD_ATTRS and not key.startswith("_"):
                payload[key] = redact_pii(value) if isinstance(value, str) else value
        if record.exc_info:
            payload["exc"] = redact_pii(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    # Route uvicorn's loggers through the JSON handler; drop its access log (we log requests ourselves).
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers[:] = []
        lg.propagate = True
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("httpx").setLevel(logging.WARNING)
