"""Text -> transaction draft (spec §5.5 "Transaction text parsing", §7.4 POST /transactions/parse).

Also used by the chat orchestrator's log_transaction intent (step 16). The LLM proposes; code
validates: category must belong to the type, date can't be in the future, amount must be > 0.
"""

import logging
import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import BaseModel

from app.ai import llm_client
from app.ai.base import AIOutputError, AIUnavailable
from app.ai.prompts import fence, render
from app.core import enums
from app.core.errors import AppError
from app.core.types import today_ist
from app.modules.finance.schemas import ParseOut, TransactionDraft
from app.modules.finance.service import CATEGORIES_BY_TYPE

log = logging.getLogger(__name__)

MAX_AMOUNT = Decimal(10_000_000)
_DIGITS = re.compile(r"\d")


class _LLMDraft(BaseModel):
    type: Literal["income", "expense"]
    amount_inr: float | None
    category: str
    occurred_on: str
    note: str | None = None
    confidence: float = 0.5


def _not_understood(issue: str) -> AppError:
    return AppError(
        "VALIDATION_ERROR",
        "I couldn't understand that as an income or expense. Try: 'spent 200 on vegetables'.",
        details=[{"field": "text", "issue": issue}],
    )


async def parse_transaction_text(text: str) -> ParseOut:
    if not _DIGITS.search(text) and not re.search(r"\b(hundred|thousand|lakh|k)\b", text, re.IGNORECASE):
        # Saves an LLM call: without any number there is no amount to record.
        raise _not_understood("no amount found")

    today = today_ist()
    prompt = render(
        "transaction_parse",
        today=f"{today:%Y-%m-%d} ({today:%A})",
        yesterday=f"{today - timedelta(days=1):%Y-%m-%d}",
        income_categories=", ".join(enums.INCOME_CATEGORIES),
        expense_categories=", ".join(enums.EXPENSE_CATEGORIES),
        message=fence(text),
    )
    try:
        result = await llm_client.chat_completion(
            [{"role": "user", "content": prompt}], json_schema=_LLMDraft, temperature=0.0, max_tokens=200
        )
    except AIUnavailable as exc:
        raise AppError("UPSTREAM_AI_UNAVAILABLE") from exc
    except AIOutputError as exc:
        raise _not_understood("could not parse") from exc
    raw: _LLMDraft = result.data

    try:
        amount = Decimal(str(raw.amount_inr)).quantize(Decimal("0.01")) if raw.amount_inr is not None else None
    except InvalidOperation:
        amount = None
    if amount is None or amount <= 0 or amount > MAX_AMOUNT:
        raise _not_understood("no valid amount")

    category = raw.category if raw.category in CATEGORIES_BY_TYPE[raw.type] else (
        "other_income" if raw.type == "income" else "other_expense"
    )
    try:
        occurred_on = date.fromisoformat(raw.occurred_on)
    except ValueError:
        occurred_on = today
    if occurred_on > today:
        occurred_on = today
    note = (raw.note or "").strip()[:200] or None

    draft = TransactionDraft(type=raw.type, amount_inr=amount, category=category, occurred_on=occurred_on, note=note)
    confidence = max(0.0, min(1.0, raw.confidence))
    if category != raw.category:
        confidence = min(confidence, 0.6)  # the model picked a category we had to replace
    return ParseOut(draft=draft, confidence=round(confidence, 2))
