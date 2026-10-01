"""Saathi orchestrator (spec §5.3): one user message in, one assistant message out.

    handle(session, user, text, input_mode, language_hint, conversation_id, want_audio)

Steps: conversation -> language -> persist user message -> pending confirmation? -> intent ->
tool -> reply (fixed text, or LLM with context + guardrail post-check) -> term highlighting ->
persist assistant message -> optional audio -> background memory work.

If the LLM is unavailable for a reply that needs it, the user message is removed again (so the app's
Retry doesn't duplicate it) and UPSTREAM_AI_UNAVAILABLE is raised.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import llm_client
from app.ai.base import AIOutputError, AIUnavailable
from app.ai.lang_detect import detect_text_language
from app.ai.prompts import fence, language_name, render
from app.core.enums import LANGUAGES
from app.core.errors import AppError
from app.core.pii import redact_pii
from app.core.storage import TTS_URL_TTL_SEC
from app.jobs import dispatch
from app.modules.chat import context as ctx
from app.modules.chat import drafts, guardrails, intents, tools
from app.modules.chat.models import Conversation, Message
from app.modules.chat.texts import NO, YES, chips, normalized_answer, t
from app.modules.finance import service as finance_service
from app.modules.finance.schemas import TransactionIn
from app.modules.goals import service as goals_service
from app.modules.goals.schemas import GoalIn
from app.modules.learn import term_detector
from app.modules.users.models import User, UserProfile
from app.modules.voice import service as voice_service

log = logging.getLogger(__name__)

NEW_CONVERSATION_AFTER = timedelta(hours=6)
TITLE_CHARS = 60
LANG_CONFIDENCE_MIN = 0.6
MAX_SUGGESTIONS = 3
SHORT_LATIN_WORDS = 4


class _Reply(BaseModel):
    reply: str = Field(min_length=1)
    suggested_replies: list[str] = Field(default_factory=list)


@dataclass
class Outcome:
    conversation: Conversation
    user_message: Message
    assistant_message: Message
    audio: dict | None


# --- Language ----------------------------------------------------------------------

def choose_language(text: str, hint: str | None, preferred: str) -> str:
    """Spec §5.3 step 2."""
    preferred = preferred if preferred in LANGUAGES else "en"
    if hint in LANGUAGES:
        return hint
    det = detect_text_language(text, fallback=preferred if preferred in ("hi", "mr") else "hi")
    if det.script == "devanagari":
        # Spec: the user's hi/mr preference decides. Otherwise trust the hi/mr detector (which
        # leans to Hindi when unsure) rather than always Hindi, so Marathi text gets Marathi.
        return preferred if preferred in ("hi", "mr") else det.language
    if det.language not in LANGUAGES or det.confidence < LANG_CONFIDENCE_MIN:
        return preferred
    # "Namaste Saathi!", "ok thanks": too short to tell English from romanized Hindi/Marathi.
    if det.script == "latin" and det.language == "en" and len(text.split()) < SHORT_LATIN_WORDS:
        return preferred
    return det.language


# --- Conversation ------------------------------------------------------------------

async def _conversation(session: AsyncSession, user: User, conversation_id: uuid.UUID | None,
                        input_mode: str) -> tuple[Conversation, bool]:
    now = datetime.now(timezone.utc)
    if conversation_id is not None:
        conv = await session.get(Conversation, conversation_id)
        if conv is None or conv.user_id != user.id:
            raise AppError("NOT_FOUND")
        if now - conv.last_message_at <= NEW_CONVERSATION_AFTER:
            return conv, False
    conv = Conversation(user_id=user.id, channel="app_voice" if input_mode == "voice" else "app_text",
                        last_message_at=now)
    session.add(conv)
    await session.flush()
    return conv, True


# --- Confirmations -----------------------------------------------------------------

async def _confirm(session: AsyncSession, user: User, draft: dict, language: str, input_mode: str) -> tools.ToolResult:
    kind, data = draft["kind"], draft["data"]
    if kind == "transaction":
        try:
            await finance_service.create_transaction(session, user, TransactionIn(
                type=data["type"], amount_inr=Decimal(str(data["amount_inr"])), category=data["category"],
                occurred_on=data["occurred_on"], note=data.get("note"),
                source="voice" if input_mode == "voice" else "chat",
            ))
        except (AppError, ValidationError) as exc:
            log.warning("chat transaction not saved", extra={"error": repr(exc)})
            return tools.ToolResult(fixed_reply=t("save_failed", language), calls=[{"tool": "transaction_create", "ok": False}])
        return tools.ToolResult(fixed_reply=t("saved_tx", language, **tools.tx_words(data, language)), pose="thumbs_up",
                                calls=[{"tool": "transaction_create", "ok": True}])
    try:
        goal = await goals_service.create_goal(session, user, GoalIn(
            title=data["title"], category=data["category"], target_amount_inr=Decimal(str(data["target_amount_inr"])),
            target_date=data.get("target_date"),
        ))
    except (AppError, ValidationError) as exc:
        log.warning("chat goal not saved", extra={"error": repr(exc)})
        return tools.ToolResult(fixed_reply=t("save_failed", language), calls=[{"tool": "goal_create", "ok": False}])
    return tools.ToolResult(
        fixed_reply=t("saved_goal", language, title=goal.title), pose="thumbs_up",
        cards=[{"type": "goal", "payload": goal.model_dump(mode="json")}],
        calls=[{"tool": "goal_create", "ok": True, "goal_id": str(goal.id)}],
    )


# --- LLM reply ---------------------------------------------------------------------

async def _llm_reply(c: ctx.Context, tool: tools.ToolResult, text: str, language: str) -> tuple[str, list[str], tuple[int, int]]:
    system = render(
        "saathi_system", language_name=language_name(language), profile_summary=c.profile_summary,
        memory_facts=c.memory_facts, goals=c.goals, finance_snapshot=c.finance_snapshot,
        conversation_summary=c.conversation_summary, tool_context=tool.tool_context,
    )
    messages = [{"role": "system", "content": system}, *c.history, {"role": "user", "content": fence(text)}]
    tokens = [0, 0]

    async def ask(extra: str | None = None) -> tuple[str, list[str]]:
        msgs = messages if extra is None else [*messages[:-1], {"role": "system", "content": extra}, messages[-1]]
        try:
            result = await llm_client.chat_completion(msgs, json_schema=_Reply, temperature=0.3, max_tokens=500)
            tokens[0] += result.tokens_in or 0
            tokens[1] += result.tokens_out or 0
            return result.data.reply.strip(), [s.strip() for s in result.data.suggested_replies if s.strip()]
        except AIOutputError as exc:  # spec §5.3 step 11: use the text, no chips
            raw = (exc.raw_text or "").strip()
            if not raw:
                raise
            return raw, []

    reply, suggested = await ask()
    problem = guardrails.violation(reply)
    if problem:
        log.warning("reply failed guardrail, regenerating", extra={"problem": problem})
        reply, suggested = await ask(guardrails.STRICTER)
        if guardrails.violation(reply):
            log.warning("reply failed guardrail twice, using fallback")
            reply, suggested = t("guardrail_fallback", language), []
    suggested = [s[:40] for s in suggested][:MAX_SUGGESTIONS]
    return reply, suggested, (tokens[0], tokens[1])


# --- Background memory work (Celery memory.extract / memory.summarize, spec §5.3 step 14) ---

async def _schedule_memory(conversation_id: uuid.UUID) -> None:
    await dispatch.enqueue("memory.extract", conversation_id)
    await dispatch.enqueue("memory.summarize", conversation_id)


async def drain_background(timeout: float | None = None) -> None:
    """Wait for in-process jobs (tests, shutdown)."""
    await dispatch.drain(timeout)


# --- Main --------------------------------------------------------------------------

async def handle(
    session: AsyncSession, user: User, text: str, *, input_mode: str = "text", language_hint: str | None = None,
    conversation_id: uuid.UUID | None = None, want_audio: bool = False,
) -> Outcome:
    text = text.strip()
    conv, created = await _conversation(session, user, conversation_id, input_mode)
    language = choose_language(text, language_hint, user.preferred_language)
    now = datetime.now(timezone.utc)
    user_msg = Message(conversation_id=conv.id, user_id=user.id, role="user", content=text, language=language,
                       input_mode=input_mode)
    session.add(user_msg)
    if conv.title is None:
        conv.title = text[:TITLE_CHARS]
    conv.last_message_at = now
    await session.commit()
    await session.refresh(user_msg)
    log.info("chat message", extra={"conversation_id": str(conv.id), "language": language, "text": redact_pii(text)[:200]})

    try:
        intent, routing, tool = await _decide(session, user, text, language, input_mode)
        if tool.fixed_reply is not None:
            reply, suggested, tokens = tool.fixed_reply, tool.suggested or [], tool.llm_tokens
        else:
            c = await ctx.build(session, user, conv, text, language, user_msg.id)
            reply, suggested, tokens = await _llm_reply(c, tool, text, language)
    except AIUnavailable as exc:
        log.warning("chat reply unavailable", extra={"error": str(exc)})
        msg_id, conv_id = user_msg.id, conv.id  # read before rollback expires the objects
        await session.rollback()
        await session.execute(delete(Message).where(Message.id == msg_id))
        if created:
            await session.execute(delete(Conversation).where(Conversation.id == conv_id))
        await session.commit()
        raise AppError("UPSTREAM_AI_UNAVAILABLE") from exc

    spans = await term_detector.detect(session, reply, language)
    pose = tool.pose or tools.pose_for(intent)
    assistant = Message(
        conversation_id=conv.id, user_id=user.id, role="assistant", content=reply, language=language,
        input_mode=input_mode, intent=intent,
        tool_calls={"calls": tool.calls, "routing": routing, "mascot_pose": pose},
        cards=tool.cards or None, highlighted_terms=[s.__dict__ for s in spans] or None,
        suggested_replies=suggested or None, tokens_in=tokens[0] or None, tokens_out=tokens[1] or None,
    )
    session.add(assistant)
    conv.last_message_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(assistant)

    audio = await _audio(session, user, reply, language, input_mode, want_audio)
    if intent != "distress":  # don't turn a crisis into stored "facts"
        await _schedule_memory(conv.id)
    return Outcome(conv, user_msg, assistant, audio)


async def _decide(session: AsyncSession, user: User, text: str, language: str,
                  input_mode: str) -> tuple[str, str, tools.ToolResult]:
    """Returns (intent, routing source, tool result)."""
    pending = await drafts.pop(user.id)
    answer = normalized_answer(text)
    if pending and pending["kind"] in ("transaction", "goal"):
        intent = "log_transaction" if pending["kind"] == "transaction" else "goal_action"
        if answer in YES:
            return intent, "confirmation", await _confirm(session, user, pending, language, input_mode)
        if answer in NO:
            return intent, "confirmation", tools.ToolResult(fixed_reply=t("cancelled", language),
                                                            calls=[{"tool": "draft", "cancelled": pending["kind"]}])
        # anything else: the draft is dropped and the message handled normally
    if pending and pending["kind"] == "goal_needs_amount" and answer not in YES | NO and not intents.DISTRESS.search(text):
        return "goal_action", "draft", await tools.goal(user, f"{pending['data']['text']}. {text}", language)

    routed = await intents.route(session, text, language)
    intent = routed.intent
    if intent == "distress":
        tool = tools.ToolResult(fixed_reply=t("distress", language), calls=[{"tool": "distress"}])
    elif intent == "out_of_scope":
        tool = tools.ToolResult(fixed_reply=t("out_of_scope", language), suggested=chips("starters", language))
    elif intent == "jargon_explain":
        tool = await tools.jargon(session, routed.entities, text, language)
    elif intent == "scam_check":
        tool = await tools.scam(session, user, routed.entities, text, language)
    elif intent == "scheme_query":
        tool = await tools.schemes(session, user, language)
    elif intent == "budget_query":
        tool = await tools.budget(session, user)
    elif intent == "log_transaction":
        tool = await tools.transaction(user, text, language)
    elif intent == "goal_action":
        tool = await tools.goal(user, text, language)
    else:  # general_finance, smalltalk
        tool = tools.ToolResult()
    return intent, routed.source, tool


async def _audio(session: AsyncSession, user: User, reply: str, language: str, input_mode: str,
                 want_audio: bool) -> dict | None:
    """Spec §5.3 step 13 / §7.4: voice in -> voice out unless voice replies are off; text -> only on request."""
    profile = await session.get(UserProfile, user.id)
    enabled = profile.voice_reply_enabled if profile else True
    if not enabled or (input_mode != "voice" and not want_audio):
        return None
    try:
        url = await voice_service.speech_url(reply, language)
    except AIUnavailable as exc:
        log.warning("reply audio unavailable", extra={"error": str(exc)})
        return None
    return {"url": url, "mime": "audio/wav", "expires_in_sec": TTS_URL_TTL_SEC} if url else None
