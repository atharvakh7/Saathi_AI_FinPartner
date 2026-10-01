"""Scheduled reminders (spec §5.10). Each returns how many notifications it created.

daily_insight / streak_reminder run every 15 min and fire once a day per user, at or after the
user's chosen time (IST). The others run on fixed schedules. Only active, onboarded users.
"""

import logging
import uuid
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import and_, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import add_months, month_start
from app.modules.finance.models import Transaction
from app.modules.goals.models import Goal
from app.modules.insights import service as insights_service
from app.modules.learn.models import UserLearningStats
from app.modules.learn.service import effective_streak
from app.modules.notifications.models import Notification
from app.modules.notifications.service import IST, _ist_day_bounds, notify, settings_for
from app.modules.planner.models import Budget
from app.modules.users.models import User, UserProfile

log = logging.getLogger(__name__)

TEXTS = {
    "income_reminder": {
        "en": ("Add your earnings", "No entries in the last week. Add what you earned or spent so your plan stays right."),
        "hi": ("अपनी कमाई जोड़ें", "पिछले हफ़्ते कोई एंट्री नहीं हुई। जो कमाया या खर्च किया, जोड़ें ताकि आपका प्लान सही रहे।"),
        "mr": ("तुमची कमाई नोंदवा", "गेल्या आठवड्यात कोणतीही नोंद नाही. कमावलेले किंवा खर्च केलेले पैसे नोंदवा, म्हणजे तुमचा प्लॅन बरोबर राहील."),
        "ta": ("உங்கள் வருமானத்தைச் சேர்க்கவும்", "கடந்த வாரம் எந்தப் பதிவும் இல்லை. உங்கள் திட்டம் சரியாக இருக்க, சம்பாதித்ததையும் செலவழித்ததையும் சேர்க்கவும்."),
    },
    "goal_reminder": {
        "en": ("Goal date coming up", "'{title}' is due on {date}. You've saved {pct}% so far."),
        "hi": ("लक्ष्य की तारीख पास है", "'{title}' की तारीख {date} है। अब तक आपने {pct}% बचा लिया है।"),
        "mr": ("ध्येयाची तारीख जवळ आली", "'{title}' ची तारीख {date} आहे. आतापर्यंत तुम्ही {pct}% बचत केली आहे."),
        "ta": ("இலக்கு தேதி நெருங்குகிறது", "'{title}' தேதி {date}. இதுவரை {pct}% சேமித்துள்ளீர்கள்."),
    },
    "lean_month_alert": {
        "en": ("Next month may be tight", "Your plan expects less money next month. Keep some aside now and spend carefully."),
        "hi": ("अगला महीना तंग हो सकता है", "आपके प्लान के अनुसार अगले महीने कम पैसे आ सकते हैं। अभी कुछ पैसे बचाकर रखें और सोच-समझकर खर्च करें।"),
        "mr": ("पुढचा महिना कठीण जाऊ शकतो", "तुमच्या प्लॅननुसार पुढच्या महिन्यात कमी पैसे येऊ शकतात. आत्ताच थोडे पैसे बाजूला ठेवा आणि जपून खर्च करा."),
        "ta": ("அடுத்த மாதம் நெருக்கடியாக இருக்கலாம்", "உங்கள் திட்டப்படி அடுத்த மாதம் குறைவான பணம் வரலாம். இப்போதே கொஞ்சம் சேமித்து, கவனமாகச் செலவிடுங்கள்."),
    },
    "streak_reminder": {
        "en": ("Keep your {n}-day streak!", "Learn one money term today to keep your streak going."),
        "hi": ("अपनी {n} दिन की लगातार सीख जारी रखें!", "आज एक पैसे से जुड़ा शब्द सीखें और अपना सिलसिला बनाए रखें।"),
        "mr": ("तुमची {n} दिवसांची साखळी चालू ठेवा!", "आज पैशांशी संबंधित एक शब्द शिका आणि साखळी कायम ठेवा."),
        "ta": ("உங்கள் {n} நாள் தொடரைத் தொடருங்கள்!", "இன்று ஒரு பணச் சொல்லைக் கற்று உங்கள் தொடரைத் தொடருங்கள்."),
    },
}


def text(kind: str, language: str, **values) -> tuple[str, str]:
    title, body = TEXTS[kind].get(language) or TEXTS[kind]["en"]
    return title.format(**values), body.format(**values)


def _eligible_users():
    return select(User).join(UserProfile, UserProfile.user_id == User.id).where(
        User.status == "active", UserProfile.onboarding_completed_at.is_not(None))


async def _sent_today(session: AsyncSession, user_id: uuid.UUID, kind: str, now: datetime) -> bool:
    start, end = _ist_day_bounds(now)
    return (await session.execute(
        select(exists().where(Notification.user_id == user_id, Notification.kind == kind,
                              Notification.created_at >= start, Notification.created_at < end))
    )).scalar_one()


def _time_reached(chosen: time, now: datetime) -> bool:
    return now.astimezone(IST).time() >= chosen


async def daily_insight(session: AsyncSession, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    count = 0
    for user in (await session.execute(_eligible_users())).scalars().all():
        prefs = await settings_for(session, user.id)
        if not prefs.daily_insight_enabled or not _time_reached(prefs.daily_insight_time, now):
            continue
        if await _sent_today(session, user.id, "daily_insight", now):
            continue
        top = await insights_service.top_unread(session, user.id, 1)
        if not top or top[0].created_at < now - timedelta(days=7):
            continue
        if await notify(session, user.id, "daily_insight", top[0].title, top[0].body, top[0].cta_route or "/insights",
                        when=now):
            count += 1
    return count


async def streak_reminder(session: AsyncSession, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    today = now.astimezone(IST).date()
    count = 0
    rows = (await session.execute(
        _eligible_users().add_columns(UserLearningStats)
        .join(UserLearningStats, UserLearningStats.user_id == User.id)
    )).all()
    for user, stats in rows:
        streak = effective_streak(stats, today)
        if streak < 2 or stats.last_active_on == today:
            continue
        prefs = await settings_for(session, user.id)
        if not prefs.streak_reminder_enabled or not _time_reached(prefs.streak_reminder_time, now):
            continue
        if await _sent_today(session, user.id, "streak_reminder", now):
            continue
        title, body = text("streak_reminder", user.preferred_language, n=streak)
        if await notify(session, user.id, "streak_reminder", title, body, "/learn", when=now):
            count += 1
    return count


async def income_reminder(session: AsyncSession, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    count = 0
    recent = exists().where(Transaction.user_id == User.id, Transaction.created_at >= now - timedelta(days=7))
    users = (await session.execute(_eligible_users().where(~recent))).scalars().all()
    for user in users:
        title, body = text("income_reminder", user.preferred_language)
        if await notify(session, user.id, "income_reminder", title, body, "/transactions/new",
                        setting="income_reminder_enabled", when=now):
            count += 1
    return count


async def goal_reminder(session: AsyncSession, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    today = now.astimezone(IST).date()
    count = 0
    rows = (await session.execute(
        _eligible_users().add_columns(Goal).join(Goal, Goal.user_id == User.id)
        .where(Goal.status == "active", Goal.target_date >= today, Goal.target_date <= today + timedelta(days=90))
    )).all()
    for user, goal in rows:
        pct = min(100, round(100 * float(goal.current_amount_inr) / float(goal.target_amount_inr))) \
            if goal.target_amount_inr else 0
        title, body = text("goal_reminder", user.preferred_language, title=goal.title,
                           date=f"{goal.target_date:%d %b %Y}", pct=pct)
        if await notify(session, user.id, "goal_reminder", title, body, f"/goals/{goal.id}",
                        setting="goal_reminder_enabled", when=now):
            count += 1
    return count


async def lean_month_alert(session: AsyncSession, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    next_month = add_months(month_start(now.astimezone(IST).date()), 1)
    count = 0
    rows = (await session.execute(
        _eligible_users().join(Budget, and_(Budget.user_id == User.id, Budget.month == next_month))
        .where(Budget.mode == "lean")
    )).scalars().all()
    for user in rows:
        title, body = text("lean_month_alert", user.preferred_language)
        if await notify(session, user.id, "lean_month_alert", title, body, "/plan",
                        setting="lean_month_alert_enabled", when=now):
            count += 1
    return count

