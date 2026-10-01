"""Tool execution by intent (spec §5.3 step 7).

Each tool returns a ToolResult: grounding text for the LLM, cards for the app, and — for flows
that must not be improvised (distress, confirmations, fraud verdicts) — a fixed reply that skips
the main LLM call.
"""

import logging
import math
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import embeddings, llm_client
from app.ai.base import AIOutputError, AIUnavailable
from app.ai.prompts import fence, render
from app.core import enums
from app.core.errors import AppError
from app.core.types import today_ist
from app.modules.chat import drafts
from app.modules.chat.intents import SCAM
from app.modules.chat.texts import category_name, chips, day, inr, t
from app.modules.finance.parse import parse_transaction_text
from app.modules.fraud import service as fraud_service
from app.modules.learn.models import GlossaryTerm, GlossaryTranslation
from app.modules.learn.service import _localized_term, _with_translation
from app.modules.planner import service as planner_service
from app.modules.schemes import service as schemes_service
from app.modules.users.models import User

log = logging.getLogger(__name__)

POSES = {
    "scam_check": "shield", "scheme_query": "point_up", "budget_query": "point_up", "smalltalk": "wave",
}
TERM_SIMILARITY = 0.55
SCAM_MIN_CHARS = 20


@dataclass
class ToolResult:
    tool_context: str = "(none)"
    cards: list[dict] = field(default_factory=list)
    calls: list[dict] = field(default_factory=list)
    fixed_reply: str | None = None      # set -> no main LLM call
    suggested: list[str] | None = None  # fixed chips (with fixed_reply)
    pose: str | None = None
    llm_tokens: tuple[int, int] = (0, 0)


def pose_for(intent: str) -> str:
    return POSES.get(intent, "speaking")


# --- jargon_explain ----------------------------------------------------------------

_term_vectors: dict[str, list[float]] = {}


async def _term_by_embedding(session: AsyncSession, query: str) -> str | None:
    """Embedding fallback (spec §5.3): nearest glossary term to the question."""
    terms = list((await session.execute(select(GlossaryTerm).where(GlossaryTerm.is_active))).scalars())
    missing = [tm for tm in terms if tm.slug not in _term_vectors]
    if missing:
        vecs = await embeddings.embed([f"{tm.term_en} ({', '.join(tm.aliases or [])}): {tm.definition_en}"
                                       for tm in missing])
        _term_vectors.update({tm.slug: v for tm, v in zip(missing, vecs)})
    q = await embeddings.embed_one(query)

    def cos(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) or 1)

    scored = sorted(((cos(q, _term_vectors[tm.slug]), tm.slug) for tm in terms if tm.slug in _term_vectors), reverse=True)
    if scored and scored[0][0] >= TERM_SIMILARITY:
        return scored[0][1]
    return None


async def _find_term(session: AsyncSession, entities: dict, text_: str, language: str) -> str | None:
    if entities.get("term_slug"):
        return entities["term_slug"]
    name = str(entities.get("term") or "").strip()
    if name:
        hit = (await session.execute(
            select(GlossaryTerm.slug)
            .outerjoin(GlossaryTranslation, GlossaryTranslation.term_id == GlossaryTerm.id)
            .where(GlossaryTerm.is_active, or_(
                func.lower(GlossaryTerm.term_en) == name.lower(), GlossaryTerm.slug == name.lower(),
                func.lower(GlossaryTranslation.term_local) == name.lower(),
                text(":n = ANY(SELECT lower(a) FROM unnest(glossary_terms.aliases) a)").bindparams(n=name.lower()),
            )).limit(1)
        )).scalar_one_or_none()
        if hit:
            return hit
    try:
        return await _term_by_embedding(session, name or text_)
    except AIUnavailable:
        return None


async def jargon(session: AsyncSession, entities: dict, text_: str, language: str) -> ToolResult:
    slug = await _find_term(session, entities, text_, language)
    if slug is None:
        return ToolResult(tool_context="No glossary entry matched. Explain simply if it is a common money term; "
                                       "otherwise say you are not sure.", calls=[{"tool": "glossary", "slug": None}])
    term, tr = (await session.execute(_with_translation(language).where(GlossaryTerm.slug == slug))).one()
    loc = _localized_term(term, tr)
    card = {"type": "term", "payload": {"slug": slug, "term": loc["term"], "definition": loc["definition"],
                                        "key_takeaway": loc["key_takeaway"]}}
    context = (
        f"Glossary entry for \"{term.term_en}\" (shown to the user as a card):\n"
        f"- Definition: {term.definition_en}\n- Example: {term.example_en}\n- Analogy: {term.analogy_en}\n"
        f"- Key takeaway: {term.key_takeaway_en}\n"
        "Answer in 2 friendly sentences using this entry; an example from the user's life helps."
    )
    return ToolResult(tool_context=context, cards=[card], calls=[{"tool": "glossary", "slug": slug}])


# --- scam_check --------------------------------------------------------------------

async def scam(session: AsyncSession, user: User, entities: dict, text_: str, language: str) -> ToolResult:
    candidate = str(entities.get("text_to_check") or "").strip()
    if len(candidate) < SCAM_MIN_CHARS:
        candidate = text_
    if len(SCAM.sub("", candidate).strip(" ?.!:;-\n")) < SCAM_MIN_CHARS:  # only "is this a scam?"
        return ToolResult(fixed_reply=t("scam_need_text", language), pose="shield",
                          calls=[{"tool": "fraud", "skipped": "no message to check"}])
    check = await fraud_service.analyze_text(session, user, candidate[:5000], source_app="other",
                                             input_type="shared_text", language=language)
    payload = check.model_dump(mode="json")
    return ToolResult(
        fixed_reply=f"{check.summary} {check.advice}",
        cards=[{"type": "fraud_result", "payload": payload}],
        suggested=chips("after_scam", language),
        pose="shield",
        calls=[{"tool": "fraud", "check_id": str(check.id), "verdict": check.verdict, "risk_score": check.risk_score}],
    )


# --- scheme_query ------------------------------------------------------------------

async def schemes(session: AsyncSession, user: User, language: str) -> ToolResult:
    items = await schemes_service.top_matches(session, user, language, limit=5)
    if not items:
        context = ("Scheme Scout found no matching schemes yet. Suggest answering a few eligibility questions on "
                   "the Schemes screen.")
        return ToolResult(tool_context=context, pose="point_up", calls=[{"tool": "schemes", "count": 0}])
    status_words = {"eligible": "likely eligible", "possibly_eligible": "may be eligible (needs more answers)"}
    lines = [f"- {s.name}: {s.benefit_summary} [{status_words.get(s.match_status, s.match_status)}]" for s in items]
    context = ("Schemes this user may get, from Scheme Scout (shown as cards; tell them to tap a card for steps):\n"
               + "\n".join(lines)
               + "\nMention that details should be confirmed on the official website before applying.")
    card = {"type": "scheme_list", "payload": {"items": [s.model_dump(mode="json") for s in items]}}
    return ToolResult(tool_context=context, cards=[card], pose="point_up",
                      calls=[{"tool": "schemes", "slugs": [s.slug for s in items]}])


# --- budget_query ------------------------------------------------------------------

async def budget(session: AsyncSession, user: User) -> ToolResult:
    ov = await planner_service.overview(session, user)
    b = ov.current_budget
    card = {"type": "budget_summary", "payload": {
        "month": b.month, "mode": b.mode, "needs_limit_inr": float(b.needs_limit_inr),
        "wants_limit_inr": float(b.wants_limit_inr), "savings_target_inr": float(b.savings_target_inr),
        "spent_needs_inr": float(b.spent_needs_inr), "spent_wants_inr": float(b.spent_wants_inr),
    }}
    if not ov.has_data:
        context = ("The user has not recorded income or expenses yet, so the plan uses only their profile estimate. "
                   "Encourage them to add this month's income and expenses for a better plan.")
    else:
        context = (
            f"This month's budget ({b.month}, a {b.mode} month):\n"
            f"- Essentials (food, rent, bills, farm inputs, loan payments): limit ₹{inr(b.needs_limit_inr)}, "
            f"spent so far ₹{inr(b.spent_needs_inr)}\n"
            f"- Extras (shopping, entertainment, other wants): limit ₹{inr(b.wants_limit_inr)}, "
            f"spent so far ₹{inr(b.spent_wants_inr)}\n"
            f"- Savings target: ₹{inr(b.savings_target_inr)}; saved so far this month ₹{inr(b.saved_so_far_inr)}\n"
            f"Emergency fund: {ov.emergency_fund.pct}% of ₹{inr(ov.emergency_fund.target_inr)}."
            + (f"\nTight months ahead: {', '.join(ov.tight_months)}." if ov.tight_months else "")
        )
    return ToolResult(tool_context=context, cards=[card], pose="point_up", calls=[{"tool": "planner", "month": b.month}])


# --- log_transaction ---------------------------------------------------------------

def tx_words(draft: dict, language: str) -> dict:
    return {"what": t(draft["type"], language, amount=inr(Decimal(str(draft["amount_inr"])))),
            "category": category_name(draft["category"], language),
            "date": day(date.fromisoformat(str(draft["occurred_on"])))}


async def transaction(user: User, text_: str, language: str) -> ToolResult:
    try:
        parsed = await parse_transaction_text(text_)
    except AppError as exc:
        if exc.code == "UPSTREAM_AI_UNAVAILABLE":
            raise AIUnavailable("transaction parser unavailable") from exc
        return ToolResult(fixed_reply=t("ask_amount_tx", language), calls=[{"tool": "transaction_parse", "ok": False}])
    draft = parsed.draft.model_dump(mode="json")
    await drafts.save(user.id, "transaction", draft)
    return ToolResult(
        fixed_reply=t("confirm_tx", language, **tx_words(draft, language)),
        cards=[{"type": "transaction_draft", "payload": draft}],
        suggested=chips("yes_no", language),
        calls=[{"tool": "transaction_parse", "ok": True, "confidence": parsed.confidence}],
    )


# --- goal_action -------------------------------------------------------------------

class _GoalDraft(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    category: str
    target_amount_inr: float | None = None
    target_date: str | None = None
    confidence: float = 0.5


def goal_words(draft: dict, language: str) -> dict:
    by = t("goal_by", language, date=day(date.fromisoformat(draft["target_date"]))) if draft.get("target_date") else ""
    return {"title": draft["title"], "amount": inr(Decimal(str(draft["target_amount_inr"]))), "by": by}


async def goal(user: User, text_: str, language: str) -> ToolResult:
    today = today_ist()
    prompt = render("goal_parse", today=f"{today:%Y-%m-%d}", goal_categories=", ".join(enums.GOAL_CATEGORIES),
                    message=fence(text_))
    try:
        result = await llm_client.chat_completion([{"role": "user", "content": prompt}], json_schema=_GoalDraft,
                                                  temperature=0.0, max_tokens=150)
        g = result.data
    except AIOutputError:
        return ToolResult(fixed_reply=t("ask_amount_goal", language), calls=[{"tool": "goal_parse", "ok": False}])
    title = re.sub(r"\s+", " ", g.title).strip()[:60] or "Goal"
    target_date = None
    if g.target_date:
        try:
            parsed = date.fromisoformat(g.target_date)
            target_date = parsed.isoformat() if parsed > today else None
        except ValueError:
            target_date = None
    category = g.category if g.category in enums.GOAL_CATEGORIES else "custom"
    if not g.target_amount_inr or g.target_amount_inr <= 0:
        await drafts.save(user.id, "goal_needs_amount", {"text": text_})
        return ToolResult(fixed_reply=t("ask_amount_goal", language), calls=[{"tool": "goal_parse", "ok": False}])
    draft = {"title": title, "category": category, "target_amount_inr": round(float(g.target_amount_inr), 2),
             "target_date": target_date}
    await drafts.save(user.id, "goal", draft)
    return ToolResult(
        fixed_reply=t("confirm_goal", language, **goal_words(draft, language)),
        suggested=chips("yes_no", language),
        calls=[{"tool": "goal_parse", "ok": True, "draft": draft}],
    )
