"""Shared API types and India-time helpers (spec: money is INR numeric(12,2); dates are IST)."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import Field, PlainSerializer

from app.core.config import settings

IST = ZoneInfo(settings.TIMEZONE)

# Money is stored as Decimal; the API sends JSON numbers (spec §7.3 shows 500.00 as a number).
Money = Annotated[Decimal, PlainSerializer(lambda v: float(v), return_type=float, when_used="json")]
MoneyIn = Annotated[Decimal, Field(max_digits=12, decimal_places=2)]
MonthStr = Annotated[str, Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", examples=["2026-09"])]


def now_ist() -> datetime:
    return datetime.now(IST)


def today_ist() -> date:
    return now_ist().date()


def month_start(d: date) -> date:
    return d.replace(day=1)


def month_bounds(month: str | None) -> tuple[date, date]:
    """'YYYY-MM' (default: current IST month) -> (first day, last day)."""
    first = date.fromisoformat(f"{month}-01") if month else month_start(today_ist())
    next_first = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    return first, next_first - timedelta(days=1)


def add_months(d: date, months: int) -> date:
    """First day of the month `months` after d's month."""
    index = d.year * 12 + (d.month - 1) + months
    return date(index // 12, index % 12 + 1, 1)


def months_between(start: date, end: date) -> int:
    """Whole calendar months from start's month to end's month (e.g. Jan→Mar = 2)."""
    return (end.year - start.year) * 12 + (end.month - start.month)
