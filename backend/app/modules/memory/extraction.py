"""Learn durable facts from a conversation (spec §5.4 steps 1–3).

1. The LLM reads the last 6 messages (plus known facts, to avoid repeats) and proposes ≤ 3 facts
   in English, third person.
2. Dedupe: cosine similarity ≥ 0.90 to an active fact of the same user -> refresh that fact
   (last_used_at, importance = max) instead of inserting.
3. Cap: at most 200 active facts per user; extras are deactivated, lowest importance first, then
   least recently used.

Facts that look like they contain personal numbers (phone, account, Aadhaar, PAN, OTP) are dropped
even if the model proposes them (spec §8.2 — never store these).

Called after each assistant reply (chat orchestrator, step 16; Celery job `memory.extract`, step 17).
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import embeddings, llm_client
from app.ai.base import AIOutputError, AIUnavailable
from app.ai.prompts import fence, render
from app.core.pii import redact_pii
from app.modules.chat.models import Conversation, Message
from app.modules.memory.models import MemoryFact

log = logging.getLogger(__name__)

WINDOW_MESSAGES = 6
MAX_NEW_FACTS = 3
DEDUPE_SIMILARITY = 0.90
MAX_ACTIVE_FACTS = 200
KNOWN_FACTS_IN_PROMPT = 40
FACT_MAX_CHARS = 200


class _Fact(BaseModel):
    category: Literal["preference", "fact", "goal_context", "concern", "behavior"]
    fact_text: str = Field(min_length=3, max_length=400)
    importance: int = Field(ge=1, le=5)


class _Facts(BaseModel):
    facts: list[_Fact] = Field(default_factory=list, max_length=10)


def _clean(text: str) -> str | None:
    text = " ".join(text.split())[:FACT_MAX_CHARS]
    if redact_pii(text) != text:  # contains something that looks like a phone/account/ID/OTP number
        return None
    return text


async def _recent_messages(session: AsyncSession, conversation_id: uuid.UUID) -> list[Message]:
    rows = (
        await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(WINDOW_MESSAGES)
        )
    ).scalars()
    ordered = list(reversed(list(rows)))
    # A crisis exchange (assistant intent "distress" and the user message it answered) is never
    # mined for facts.
    skip: set = set()
    for i, m in enumerate(ordered):
        if m.role == "assistant" and m.intent == "distress":
            skip.add(m.id)
            if i > 0 and ordered[i - 1].role == "user":
                skip.add(ordered[i - 1].id)
    return [m for m in ordered if m.id not in skip]


async def _known_facts(session: AsyncSession, user_id: uuid.UUID) -> list[str]:
    rows = (
        await session.execute(
            select(MemoryFact.fact_text)
            .where(MemoryFact.user_id == user_id, MemoryFact.is_active)
            .order_by(MemoryFact.importance.desc(), MemoryFact.created_at.desc())
            .limit(KNOWN_FACTS_IN_PROMPT)
        )
    ).scalars()
    return list(rows)


async def enforce_cap(session: AsyncSession, user_id: uuid.UUID, cap: int = MAX_ACTIVE_FACTS) -> int:
    """Deactivate facts beyond the cap. Returns how many were deactivated."""
    active = (
        await session.execute(
            select(func.count(MemoryFact.id)).where(MemoryFact.user_id == user_id, MemoryFact.is_active)
        )
    ).scalar_one()
    excess = active - cap
    if excess <= 0:
        return 0
    victims = (
        await session.execute(
            select(MemoryFact.id)
            .where(MemoryFact.user_id == user_id, MemoryFact.is_active)
            .order_by(
                MemoryFact.importance.asc(),
                func.coalesce(MemoryFact.last_used_at, MemoryFact.created_at).asc(),
            )
            .limit(excess)
        )
    ).scalars()
    ids = list(victims)
    await session.execute(update(MemoryFact).where(MemoryFact.id.in_(ids)).values(is_active=False))
    return len(ids)


async def extract_facts(session: AsyncSession, conversation_id: uuid.UUID) -> dict[str, int]:
    """Returns counts {"inserted", "refreshed", "dropped"}. Never raises for AI failures."""
    counts = {"inserted": 0, "refreshed": 0, "dropped": 0}
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None:
        return counts
    messages = await _recent_messages(session, conversation_id)
    if not any(m.role == "user" for m in messages):
        return counts

    transcript = "\n".join(f"{'User' if m.role == 'user' else 'Saathi'}: {m.content}" for m in messages)
    known = await _known_facts(session, conversation.user_id)
    prompt = render(
        "memory_extract",
        existing_facts="\n".join(f"- {f}" for f in known) or "(none)",
        conversation=fence(transcript, "conversation"),
    )
    try:
        result = await llm_client.chat_completion(
            [{"role": "user", "content": prompt}], json_schema=_Facts, temperature=0.1, max_tokens=400
        )
    except (AIUnavailable, AIOutputError) as exc:
        log.warning("memory extraction skipped", extra={"error": repr(exc)})
        return counts

    proposed = []
    for fact in result.data.facts[:MAX_NEW_FACTS]:
        text = _clean(fact.fact_text)
        if text is None:
            counts["dropped"] += 1
            continue
        proposed.append((fact, text))
    if not proposed:
        return counts

    try:
        vectors = await embeddings.embed([text for _, text in proposed])
    except AIUnavailable as exc:
        log.warning("memory extraction skipped: embeddings unavailable", extra={"error": str(exc)})
        return counts

    source_id = next((m.id for m in reversed(messages) if m.role == "user"), None)
    now = datetime.now(timezone.utc)
    for (fact, text), vec in zip(proposed, vectors):
        distance = MemoryFact.embedding.cosine_distance(vec).label("distance")
        nearest = (
            await session.execute(
                select(MemoryFact, distance)
                .where(MemoryFact.user_id == conversation.user_id, MemoryFact.is_active)
                .order_by(distance)
                .limit(1)
            )
        ).first()
        if nearest is not None and 1.0 - float(nearest.distance) >= DEDUPE_SIMILARITY:
            existing = nearest[0]
            existing.last_used_at = now
            existing.importance = max(existing.importance, fact.importance)
            counts["refreshed"] += 1
            continue
        session.add(MemoryFact(
            user_id=conversation.user_id, category=fact.category, fact_text=text, embedding=vec,
            importance=fact.importance, source_message_id=source_id,
        ))
        await session.flush()  # so the next proposed fact can dedupe against this one
        counts["inserted"] += 1

    await enforce_cap(session, conversation.user_id)
    await session.commit()
    log.info("memory extracted", extra={"conversation_id": str(conversation_id), **counts})
    return counts
