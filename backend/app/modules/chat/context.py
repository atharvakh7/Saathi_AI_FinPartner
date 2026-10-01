"""Prompt context (spec §5.3 step 6): profile, recalled memory, goals, this month's money,
conversation summary and the last 10 messages."""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat.models import Conversation, Message
from app.modules.chat.texts import inr
from app.modules.finance.summary import get_summary
from app.modules.goals import service as goals_service
from app.modules.memory import retrieval
from app.modules.users.models import User, UserProfile

HISTORY_MESSAGES = 10
MAX_GOALS = 3
LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "mr": "Marathi", "ta": "Tamil"}


@dataclass
class Context:
    profile_summary: str
    memory_facts: str
    goals: str
    finance_snapshot: str
    conversation_summary: str
    history: list[dict]  # [{"role": "user"|"assistant", "content": str}], oldest first
    first_name: str | None
    occupation: str | None


def first_name(profile: UserProfile | None) -> str | None:
    name = (profile.full_name or "").strip() if profile else ""
    return name.split()[0] if name else None


def profile_summary(profile: UserProfile | None, language: str) -> str:
    if profile is None:
        return f"- Not filled in yet.\n- Language: {LANGUAGE_NAMES.get(language, language)}"
    lines = []
    if profile.full_name:
        lines.append(f"- Name: {profile.full_name}")
    if profile.age_years:
        lines.append(f"- Age: {profile.age_years}")
    if profile.state_code:
        place = f"{profile.district}, {profile.state_code}" if profile.district else profile.state_code
        lines.append(f"- Lives in: {place} ({profile.area_type or 'area unknown'})")
    if profile.occupation_type:
        lines.append(f"- Work: {profile.occupation_type.replace('_', ' ')}")
    if profile.income_pattern:
        lines.append(f"- Income pattern: {profile.income_pattern.replace('_', ' ')}")
    lo, hi = profile.declared_monthly_income_min_inr, profile.declared_monthly_income_max_inr
    if hi:
        lines.append(f"- Monthly income (their estimate): ₹{inr(lo or 0)}–₹{inr(hi)}")
    if profile.household_size:
        lines.append(f"- Household: {profile.household_size} people")
    lines.append(f"- Language: {LANGUAGE_NAMES.get(language, language)}")
    return "\n".join(lines)


async def goals_text(session: AsyncSession, user: User) -> str:
    goals = (await goals_service.list_goals(session, user, "active"))[:MAX_GOALS]
    if not goals:
        return "(no active goals)"
    out = []
    for g in goals:
        line = f"- {g.title}: ₹{inr(g.current_amount_inr)} saved of ₹{inr(g.target_amount_inr)} ({g.progress_pct}%)"
        if g.target_date:
            line += f", target date {g.target_date:%d %b %Y}"
        out.append(line)
    return "\n".join(out)


async def finance_text(session: AsyncSession, user_id: uuid.UUID) -> str:
    s = await get_summary(session, user_id, None)
    if not s.has_transactions:
        return "(no income or expenses recorded yet)"
    lines = [
        f"- {s.month}: income ₹{inr(s.income_inr)}, expenses ₹{inr(s.expenses_inr)}, saved ₹{inr(s.savings_inr)}",
    ]
    if s.debt_outstanding_inr:
        lines.append(f"- Loans outstanding: ₹{inr(s.debt_outstanding_inr)}")
    if s.emergency_fund.exists:
        lines.append(f"- Emergency fund: {s.emergency_fund.pct}% of target")
    if s.risk:
        lines.append(f"- Money risk level: {s.risk.level}")
    return "\n".join(lines)


async def history(session: AsyncSession, conversation_id: uuid.UUID, before_id: uuid.UUID | None) -> list[dict]:
    stmt = select(Message).where(Message.conversation_id == conversation_id)
    if before_id is not None:
        stmt = stmt.where(Message.id != before_id)
    rows = (await session.execute(
        stmt.order_by(Message.created_at.desc(), Message.id.desc()).limit(HISTORY_MESSAGES)
    )).scalars()
    return [{"role": m.role, "content": m.content} for m in reversed(list(rows))]


async def build(
    session: AsyncSession, user: User, conversation: Conversation, text: str, language: str,
    current_message_id: uuid.UUID | None,
) -> Context:
    profile = await session.get(UserProfile, user.id)
    facts = await retrieval.retrieve(session, user.id, text)
    return Context(
        profile_summary=profile_summary(profile, language),
        memory_facts=retrieval.format_for_prompt(facts),
        goals=await goals_text(session, user),
        finance_snapshot=await finance_text(session, user.id),
        conversation_summary=conversation.summary or "(new conversation)",
        history=await history(session, conversation.id, current_message_id),
        first_name=first_name(profile),
        occupation=profile.occupation_type if profile else None,
    )
