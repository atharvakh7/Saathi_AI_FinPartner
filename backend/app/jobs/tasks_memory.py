"""memory.extract / memory.summarize (spec §5.3 step 14, §5.4)."""

import uuid

from app.core.db import SessionLocal
from app.jobs.registry import task
from app.modules.memory import extraction
from app.modules.memory import service as memory_service


@task("memory.extract")
async def extract(conversation_id: str) -> dict:
    async with SessionLocal() as session:
        return await extraction.extract_facts(session, uuid.UUID(conversation_id))


@task("memory.summarize")
async def summarize(conversation_id: str) -> bool:
    async with SessionLocal() as session:
        return await memory_service.summarize_conversation(session, uuid.UUID(conversation_id))
