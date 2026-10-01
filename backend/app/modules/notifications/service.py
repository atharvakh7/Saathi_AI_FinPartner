"""In-app notifications + push delivery (spec §5.10, §7.4 /notifications).

Every notification is stored (the in-app list shows it). Push rules:
- per-kind user setting off -> not created at all; `push_enabled` off or no device -> stored, status 'skipped'
- quiet hours 22:00–07:00 IST -> scheduled for 07:00
- at most PUSH_MAX_PER_DAY pushes per user per IST day -> the rest are 'skipped' (still in the list)
`dispatch_due()` sends queued notifications whose time has come; DeviceNotRegistered tokens are deleted.
"""

import logging
import uuid
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError
from app.core.pagination import after_cursor, decode_cursor, encode_cursor
from app.modules.notifications import expo
from app.modules.notifications.models import Notification
from app.modules.users.models import DeviceToken, NotificationSettings

log = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")
QUIET_START, QUIET_END = time(22, 0), time(7, 0)
DISPATCH_BATCH = 500


def defaults() -> NotificationSettings:
    return NotificationSettings(push_enabled=True, daily_insight_enabled=True, daily_insight_time=time(9, 0),
                                income_reminder_enabled=True, goal_reminder_enabled=True, scheme_deadline_enabled=True,
                                lean_month_alert_enabled=True, streak_reminder_enabled=True,
                                streak_reminder_time=time(20, 0))


async def settings_for(session: AsyncSession, user_id: uuid.UUID) -> NotificationSettings:
    return await session.get(NotificationSettings, user_id) or defaults()


def after_quiet_hours(when: datetime) -> datetime:
    local = when.astimezone(IST)
    t = local.timetz().replace(tzinfo=None)
    if t >= QUIET_START:
        local = (local + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)
    elif t < QUIET_END:
        local = local.replace(hour=7, minute=0, second=0, microsecond=0)
    return local.astimezone(timezone.utc)


def _ist_day_bounds(when: datetime) -> tuple[datetime, datetime]:
    local = when.astimezone(IST)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.astimezone(timezone.utc), (start + timedelta(days=1)).astimezone(timezone.utc)


async def notify(
    session: AsyncSession, user_id: uuid.UUID, kind: str, title: str, body: str, route: str | None = None, *,
    setting: str | None = None, when: datetime | None = None,
) -> Notification | None:
    """Create a notification. `setting`: the NotificationSettings flag that must be on (else nothing)."""
    prefs = await settings_for(session, user_id)
    if setting and not getattr(prefs, setting):
        return None
    scheduled = after_quiet_hours(when or datetime.now(timezone.utc))
    start, end = _ist_day_bounds(scheduled)
    pushes_that_day = (await session.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id, Notification.status.in_(("queued", "sent")),
            Notification.scheduled_for >= start, Notification.scheduled_for < end)
    )).scalar_one()
    status = "queued" if prefs.push_enabled and pushes_that_day < settings.PUSH_MAX_PER_DAY else "skipped"
    n = Notification(user_id=user_id, kind=kind, title=title[:120], body=body[:300],
                     data={"route": route} if route else None, status=status, scheduled_for=scheduled)
    session.add(n)
    await session.commit()
    return n


async def dispatch_due(session: AsyncSession, now: datetime | None = None) -> dict[str, int]:
    now = now or datetime.now(timezone.utc)
    due = list((await session.execute(
        select(Notification).where(Notification.status == "queued", Notification.scheduled_for <= now)
        .order_by(Notification.scheduled_for).limit(DISPATCH_BATCH).with_for_update(skip_locked=True)
    )).scalars())
    counts = {"sent": 0, "failed": 0, "skipped": 0, "tokens_removed": 0}
    if not due:
        await session.commit()
        return counts
    user_ids = {n.user_id for n in due}
    tokens: dict[uuid.UUID, list[DeviceToken]] = {u: [] for u in user_ids}
    for t in (await session.execute(select(DeviceToken).where(DeviceToken.user_id.in_(user_ids)))).scalars():
        tokens[t.user_id].append(t)

    messages, owners = [], []  # owners[i] = (notification, token) for messages[i]
    for n in due:
        if not tokens[n.user_id]:
            n.status = "skipped"
            counts["skipped"] += 1
            continue
        for t in tokens[n.user_id]:
            messages.append({"to": t.expo_push_token, "title": n.title, "body": n.body, "sound": "default",
                             "data": {**(n.data or {}), "notification_id": str(n.id)}})
            owners.append((n, t))
    tickets = await expo.send(messages) if messages else []

    delivered: dict[uuid.UUID, bool] = {}
    dead: set[uuid.UUID] = set()
    for (n, t), ticket in zip(owners, tickets):
        delivered[n.id] = delivered.get(n.id, False) or ticket.ok
        if ticket.error == "DeviceNotRegistered":
            dead.add(t.id)
    for n in due:
        if n.status == "skipped":
            continue
        if delivered.get(n.id):
            n.status, n.sent_at = "sent", now
            counts["sent"] += 1
        else:
            n.status = "failed"
            counts["failed"] += 1
    if dead:
        await session.execute(delete(DeviceToken).where(DeviceToken.id.in_(dead)))
        counts["tokens_removed"] = len(dead)
    await session.commit()
    if any(counts.values()):
        log.info("push dispatch", extra=counts)
    return counts


# --- /notifications ----------------------------------------------------------------

async def list_notifications(session: AsyncSession, user_id: uuid.UUID, limit: int, cursor: str | None):
    stmt = select(Notification).where(Notification.user_id == user_id)
    if cursor:
        stmt = stmt.where(after_cursor([Notification.created_at, Notification.id],
                                       decode_cursor(cursor, [datetime.fromisoformat, uuid.UUID])))
    rows = list((await session.execute(
        stmt.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit + 1)
    )).scalars())
    page = rows[:limit]
    return page, (encode_cursor([page[-1].created_at, page[-1].id]) if len(rows) > limit else None)


async def mark_read(session: AsyncSession, user_id: uuid.UUID, notification_id: uuid.UUID) -> None:
    n = await session.get(Notification, notification_id)
    if n is None or n.user_id != user_id:
        raise AppError("NOT_FOUND")
    if n.read_at is None:
        n.read_at = datetime.now(timezone.utc)
    await session.commit()


async def mark_all_read(session: AsyncSession, user_id: uuid.UUID) -> None:
    await session.execute(
        update(Notification).where(Notification.user_id == user_id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(timezone.utc))
    )
    await session.commit()
