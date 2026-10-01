"""Keyset pagination: `?limit=30&cursor=<opaque>` -> `{items, next_cursor}` (spec §7)."""

import base64
import json
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import and_, or_

from app.core.errors import AppError

T = TypeVar("T")

DEFAULT_LIMIT = 30
MAX_LIMIT = 100


class Page(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None


def encode_cursor(values: Sequence[Any]) -> str:
    raw = json.dumps([v.isoformat() if hasattr(v, "isoformat") else str(v) for v in values])
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def decode_cursor(cursor: str, parsers: Sequence) -> list:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = json.loads(base64.urlsafe_b64decode(padded.encode()))
        if len(raw) != len(parsers):
            raise ValueError
        return [parse(v) for parse, v in zip(parsers, raw)]
    except Exception as exc:
        raise AppError("VALIDATION_ERROR", details=[{"field": "cursor", "issue": "invalid cursor"}]) from exc


def after_cursor(columns: Sequence, values: Sequence, descending: bool = True):
    """WHERE clause for rows strictly after `values` in (col1, col2, ...) order."""
    clauses = []
    for i, col in enumerate(columns):
        equal = [c == v for c, v in zip(columns[:i], values[:i])]
        beyond = col < values[i] if descending else col > values[i]
        clauses.append(and_(*equal, beyond))
    return or_(*clauses)


def clamp_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_LIMIT
    if not 1 <= limit <= MAX_LIMIT:
        raise AppError("VALIDATION_ERROR", details=[{"field": "limit", "issue": f"must be 1–{MAX_LIMIT}"}])
    return limit
