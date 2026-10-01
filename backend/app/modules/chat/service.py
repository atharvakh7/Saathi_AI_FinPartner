"""Conversations, message history and the greeting (spec §7.4 /chat/*)."""

import json
import logging
import uuid
from datetime import datetime

from pydantic import BaseModel, Field
from redis.exceptions import RedisError
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import llm_client
from app.ai.base import AIOutputError, AIUnavailable
from app.ai.prompts import language_name, render
from app.core.errors import AppError
from app.core.pagination import after_cursor, decode_cursor, encode_cursor
from app.core.redis import redis_client
from app.core.types import now_ist
from app.modules.chat.context import first_name
from app.modules.chat.models import Conversation, Message
from app.modules.chat.schemas import ChatMessageOut, ConversationItem, ConversationPage, GreetingOut, MessagePage
from app.modules.chat.texts import category_name, chips, inr, t
from app.modules.finance.models import Transaction
from app.modules.goals import service as goals_service
from app.modules.insights.models import Insight
from app.modules.users.models import User, UserProfile

log = logging.getLogger(__name__)

GREETING_CACHE_SEC = 6 * 3600
GREETING_MAX_CHARS = 220


def message_out(m: Message) -> ChatMessageOut:
    meta = m.tool_calls if isinstance(m.tool_calls, dict) else {}
    return ChatMessageOut(
        id=m.id, role=m.role, content=m.content, language=m.language, input_mode=m.input_mode, intent=m.intent,
        highlighted_terms=m.highlighted_terms or [], cards=m.cards or [], suggested_replies=m.suggested_replies or [],
        mascot_pose=meta.get("mascot_pose") if m.role == "assistant" else None, created_at=m.created_at,
    )


async def list_conversations(session: AsyncSession, user: User, limit: int, cursor: str | None) -> ConversationPage:
    stmt = select(Conversation).where(Conversation.user_id == user.id, ~Conversation.is_archived)
    if cursor:
        stmt = stmt.where(after_cursor([Conversation.last_message_at, Conversation.id],
                                       decode_cursor(cursor, [datetime.fromisoformat, uuid.UUID])))
    rows = list((await session.execute(
        stmt.order_by(Conversation.last_message_at.desc(), Conversation.id.desc()).limit(limit + 1)
    )).scalars())
    page = rows[:limit]
    return ConversationPage(
        items=[ConversationItem(id=c.id, title=c.title, channel=c.channel, last_message_at=c.last_message_at)
               for c in page],
        next_cursor=encode_cursor([page[-1].last_message_at, page[-1].id]) if len(rows) > limit else None,
    )


async def _own_conversation(session: AsyncSession, user: User, conversation_id: uuid.UUID) -> Conversation:
    conv = await session.get(Conversation, conversation_id)
    if conv is None or conv.user_id != user.id:
        raise AppError("NOT_FOUND")
    return conv


async def list_messages(session: AsyncSession, user: User, conversation_id: uuid.UUID, limit: int,
                        cursor: str | None) -> MessagePage:
    await _own_conversation(session, user, conversation_id)
    stmt = select(Message).where(Message.conversation_id == conversation_id)
    if cursor:
        stmt = stmt.where(after_cursor([Message.created_at, Message.id],
                                       decode_cursor(cursor, [datetime.fromisoformat, uuid.UUID])))
    rows = list((await session.execute(
        stmt.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit + 1)
    )).scalars())
    page = rows[:limit]
    return MessagePage(
        items=[message_out(m) for m in page],
        next_cursor=encode_cursor([page[-1].created_at, page[-1].id]) if len(rows) > limit else None,
    )


async def delete_conversation(session: AsyncSession, user: User, conversation_id: uuid.UUID) -> None:
    """Messages go with it (CASCADE); memory facts learned from them stay (source -> NULL), and can be
    removed on the Memory screen."""
    await _own_conversation(session, user, conversation_id)
    await session.execute(delete(Conversation).where(Conversation.id == conversation_id))
    await session.commit()


# --- Greeting ----------------------------------------------------------------------

class _Greeting(BaseModel):
    text: str = Field(min_length=2)
    suggested_replies: list[str] = Field(default_factory=list)


def _time_of_day() -> str:
    hour = now_ist().hour
    return "morning" if 4 <= hour < 12 else "afternoon" if hour < 17 else "evening"


async def _greeting_facts(session: AsyncSession, user: User, language: str) -> dict:
    goals = await goals_service.list_goals(session, user, "active")
    top_goal = "none"
    if goals:
        g = goals[0]
        top_goal = f"{g.title} ({g.progress_pct}% of ₹{inr(g.target_amount_inr)} saved)"
    insight = (await session.execute(
        select(Insight.title).where(Insight.user_id == user.id, ~Insight.is_read)
        .order_by(Insight.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    last = (await session.execute(
        select(Transaction).where(Transaction.user_id == user.id)
        .order_by(Transaction.occurred_on.desc(), Transaction.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    last_entry = "nothing recorded yet"
    if last is not None:
        last_entry = f"{last.type} for {category_name(last.category, 'en')} on {last.occurred_on:%d %b}"
    return {"top_goal": top_goal, "top_insight": insight or "none", "last_entry": last_entry}


def _static_greeting(name: str | None, language: str) -> GreetingOut:
    text_ = t("greeting_fallback", language, name=name or "").replace(" !", "!").replace("  ", " ")
    return GreetingOut(text=text_, suggested_replies=chips("greeting", language))


async def greeting(session: AsyncSession, user: User, language: str) -> GreetingOut:
    key = f"greeting:{user.id}:{language}"
    try:
        cached = await redis_client.get(key)
        if cached:
            return GreetingOut(**json.loads(cached))
    except RedisError:
        pass
    profile = await session.get(UserProfile, user.id)
    name = first_name(profile)
    facts = await _greeting_facts(session, user, language)
    prompt = render("greeting", language_name=language_name(language), first_name=name or "(unknown)",
                    time_of_day=_time_of_day(), **facts)
    try:
        result = await llm_client.chat_completion([{"role": "user", "content": prompt}], json_schema=_Greeting,
                                                  temperature=0.3, max_tokens=150, timeout=30)
        g = result.data
        if len(g.text) > GREETING_MAX_CHARS:
            raise AIOutputError("greeting too long")
        out = GreetingOut(text=g.text.strip(),
                          suggested_replies=[s.strip()[:40] for s in g.suggested_replies if s.strip()][:3]
                          or chips("greeting", language))
    except (AIUnavailable, AIOutputError) as exc:
        log.warning("greeting fell back to static text", extra={"error": repr(exc)})
        return _static_greeting(name, language)  # not cached: try the LLM again next time
    try:
        await redis_client.set(key, out.model_dump_json(), ex=GREETING_CACHE_SEC)
    except RedisError:
        pass
    return out
