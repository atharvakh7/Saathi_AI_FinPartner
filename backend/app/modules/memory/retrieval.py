"""Find the facts most relevant to a message (spec §5.4 step 4, §5.3 step 6).

Nearest neighbours by cosine distance (pgvector HNSW index), then a light importance weighting:
score = similarity × (0.9 + 0.025 × importance), so importance 5 beats importance 1 only when the
two are about equally relevant. Returned facts get `last_used_at` updated (used by the cap).
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import embeddings
from app.ai.base import AIUnavailable
from app.modules.memory.models import MemoryFact

log = logging.getLogger(__name__)

TOP_K = 5
CANDIDATES = 15


@dataclass(frozen=True)
class RecalledFact:
    id: uuid.UUID
    category: str
    fact_text: str
    importance: int
    similarity: float


def _weighted(similarity: float, importance: int) -> float:
    return similarity * (0.9 + 0.025 * importance)


async def retrieve(session: AsyncSession, user_id: uuid.UUID, query_text: str, k: int = TOP_K) -> list[RecalledFact]:
    """Top-k facts for this user; [] when embeddings are unavailable (chat continues without memory)."""
    if not query_text.strip():
        return []
    try:
        query_vec = await embeddings.embed_one(query_text)
    except AIUnavailable as exc:
        log.warning("memory retrieval skipped", extra={"error": str(exc)})
        return []
    distance = MemoryFact.embedding.cosine_distance(query_vec).label("distance")
    rows = (
        await session.execute(
            select(MemoryFact.id, MemoryFact.category, MemoryFact.fact_text, MemoryFact.importance, distance)
            .where(MemoryFact.user_id == user_id, MemoryFact.is_active)
            .order_by(distance)
            .limit(CANDIDATES)
        )
    ).all()
    facts = [RecalledFact(r.id, r.category, r.fact_text, r.importance, 1.0 - float(r.distance)) for r in rows]
    facts.sort(key=lambda f: _weighted(f.similarity, f.importance), reverse=True)
    chosen = facts[:k]
    if chosen:
        await session.execute(
            update(MemoryFact)
            .where(MemoryFact.id.in_([f.id for f in chosen]))
            .values(last_used_at=datetime.now(timezone.utc))
        )
        await session.commit()
    return chosen


def format_for_prompt(facts: list[RecalledFact]) -> str:
    """Bullet list for the {{memory_facts}} slot of saathi_system.md."""
    if not facts:
        return "(nothing remembered yet)"
    return "\n".join(f"- {f.fact_text}" for f in facts)
