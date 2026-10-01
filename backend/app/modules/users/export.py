"""GET /me/export — everything stored about the user (DPDP right to access, spec §7.4, §8.4)."""

from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat.models import Conversation, Message
from app.modules.finance.models import Debt, Transaction
from app.modules.fraud.models import FraudCheck
from app.modules.goals.models import Goal, GoalContribution
from app.modules.insights.models import Insight
from app.modules.learn.models import LessonProgress, TermFeedback, UserLearningStats
from app.modules.memory.models import MemoryFact
from app.modules.notifications.models import Notification
from app.modules.schemes.models import UserSchemeTracking
from app.modules.users.models import Consent, NotificationSettings, User, UserProfile

# Internal columns that are meaningless or sensitive outside the system.
_EXCLUDE = {"embedding", "user_id"}


def row_to_dict(obj, exclude: set[str] = frozenset()) -> dict[str, Any]:
    return {
        attr.key: getattr(obj, attr.key)
        for attr in inspect(obj).mapper.column_attrs
        if attr.key not in _EXCLUDE and attr.key not in exclude
    }


async def _all(session: AsyncSession, model, user_id, order_by=None) -> list:
    stmt = select(model).where(model.user_id == user_id)
    if order_by is not None:
        stmt = stmt.order_by(order_by)
    return list((await session.execute(stmt)).scalars())


async def build_export(session: AsyncSession, user: User) -> dict[str, Any]:
    uid = user.id
    profile = await session.get(UserProfile, uid)
    settings_row = await session.get(NotificationSettings, uid)
    stats = await session.get(UserLearningStats, uid)

    conversations = []
    for conv in await _all(session, Conversation, uid, Conversation.created_at):
        messages = (
            await session.execute(
                select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at)
            )
        ).scalars()
        conversations.append({**row_to_dict(conv), "messages": [row_to_dict(m) for m in messages]})

    goals = []
    for goal in await _all(session, Goal, uid, Goal.created_at):
        contributions = (
            await session.execute(
                select(GoalContribution)
                .where(GoalContribution.goal_id == goal.id)
                .order_by(GoalContribution.contributed_on)
            )
        ).scalars()
        goals.append({**row_to_dict(goal), "contributions": [row_to_dict(c, {"goal_id"}) for c in contributions]})

    data = {
        "exported_at": datetime.now(timezone.utc),
        "user": row_to_dict(user),
        "profile": row_to_dict(profile) if profile else None,
        "consents": [row_to_dict(c) for c in await _all(session, Consent, uid, Consent.created_at)],
        "notification_settings": row_to_dict(settings_row) if settings_row else None,
        "conversations": conversations,
        "memory_facts": [row_to_dict(m) for m in await _all(session, MemoryFact, uid, MemoryFact.created_at)],
        "transactions": [row_to_dict(t) for t in await _all(session, Transaction, uid, Transaction.occurred_on)],
        "debts": [row_to_dict(d) for d in await _all(session, Debt, uid, Debt.created_at)],
        "goals": goals,
        "insights": [row_to_dict(i) for i in await _all(session, Insight, uid, Insight.created_at)],
        "notifications": [row_to_dict(n) for n in await _all(session, Notification, uid, Notification.created_at)],
        "fraud_checks": [row_to_dict(f) for f in await _all(session, FraudCheck, uid, FraudCheck.created_at)],
        "scheme_tracking": [row_to_dict(s) for s in await _all(session, UserSchemeTracking, uid)],
        "learning": {
            "stats": row_to_dict(stats) if stats else None,
            "completed_lessons": [row_to_dict(p) for p in await _all(session, LessonProgress, uid)],
            "term_feedback": [row_to_dict(f) for f in await _all(session, TermFeedback, uid)],
        },
    }
    return jsonable_encoder(data)
