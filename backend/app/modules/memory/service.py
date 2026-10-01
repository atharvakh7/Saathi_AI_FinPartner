"""Memory facts CRUD and rolling conversation summaries (spec §5.4, §7.4 /memory).

Summaries (§5.4 step 5): once a conversation has more than 30 messages and at least 20 messages
are not yet covered, everything except the last 10 messages is folded into conversations.summary
(≤ 150 words, English). `summary_updated_at` stores the created_at of the last message included,
so the next run only adds what came after it.
"""

import logging
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import llm_client
from app.ai.base import AIOutputError, AIUnavailable
from app.ai.prompts import fence, render
from app.core.errors import AppError
from app.modules.chat.models import Conversation, Message
from app.modules.memory.models import MemoryFact
from app.modules.users.models import User

log = logging.getLogger(__name__)

SUMMARY_MIN_MESSAGES = 30
SUMMARY_NEW_MESSAGES = 20
SUMMARY_KEEP_RECENT = 10
SUMMARY_MAX_WORDS = 150


# --- /memory -----------------------------------------------------------------------

async def list_facts(session: AsyncSession, user: User) -> list[MemoryFact]:
    rows = await session.execute(
        select(MemoryFact)
        .where(MemoryFact.user_id == user.id, MemoryFact.is_active)
        .order_by(MemoryFact.created_at.desc())
    )
    return list(rows.scalars())


async def delete_fact(session: AsyncSession, user: User, fact_id: uuid.UUID) -> None:
    """Hard delete: the user asked Saathi to forget it."""
    result = await session.execute(delete(MemoryFact).where(MemoryFact.id == fact_id, MemoryFact.user_id == user.id))
    if result.rowcount == 0:
        raise AppError("NOT_FOUND")
    await session.commit()


async def delete_all_facts(session: AsyncSession, user: User) -> int:
    """Forget everything, including facts previously deactivated by the cap."""
    result = await session.execute(delete(MemoryFact).where(MemoryFact.user_id == user.id))
    await session.commit()
    return result.rowcount


# --- Rolling summaries -------------------------------------------------------------

async def needs_summary(session: AsyncSession, conversation: Conversation) -> bool:
    total = (
        await session.execute(select(func.count(Message.id)).where(Message.conversation_id == conversation.id))
    ).scalar_one()
    if total <= SUMMARY_MIN_MESSAGES:
        return False
    stmt = select(func.count(Message.id)).where(Message.conversation_id == conversation.id)
    if conversation.summary_updated_at is not None:
        stmt = stmt.where(Message.created_at > conversation.summary_updated_at)
    uncovered = (await session.execute(stmt)).scalar_one()
    return uncovered >= SUMMARY_NEW_MESSAGES


async def summarize_conversation(session: AsyncSession, conversation_id: uuid.UUID, force: bool = False) -> bool:
    """Returns True when the summary was updated. Never raises for AI failures."""
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None or (not force and not await needs_summary(session, conversation)):
        return False

    recent = (
        await session.execute(
            select(Message.created_at)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .offset(SUMMARY_KEEP_RECENT - 1)
            .limit(1)
        )
    ).scalar_one_or_none()
    if recent is None:
        return False  # fewer than 10 messages
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id, Message.created_at < recent)
        .order_by(Message.created_at, Message.id)
    )
    if conversation.summary_updated_at is not None:
        stmt = stmt.where(Message.created_at > conversation.summary_updated_at)
    to_fold = list((await session.execute(stmt)).scalars())
    if not to_fold:
        return False

    transcript = "\n".join(f"{'User' if m.role == 'user' else 'Saathi'}: {m.content}" for m in to_fold)
    prompt = render(
        "summarize",
        previous_summary=conversation.summary or "(none)",
        conversation=fence(transcript, "conversation"),
    )
    try:
        result = await llm_client.chat_completion(
            [{"role": "user", "content": prompt}], temperature=0.2, max_tokens=300
        )
    except (AIUnavailable, AIOutputError) as exc:
        log.warning("conversation summary skipped", extra={"error": repr(exc)})
        return False
    words = result.text.strip().split()
    if not words:
        return False
    conversation.summary = " ".join(words[:SUMMARY_MAX_WORDS])
    conversation.summary_updated_at = to_fold[-1].created_at
    await session.commit()
    return True
