"""/chat/* endpoints (spec §4.7 S22, §7.4). /chat/transcribe and /chat/tts are in the voice module."""

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.i18n import resolve_language
from app.core.rate_limit import rate_limit
from app.core.security import get_current_user
from app.modules.chat import orchestrator, service
from app.modules.chat.schemas import ChatIn, ChatOut, ConversationPage, GreetingOut, Language, MessagePage, VoiceChatOut
from app.modules.users.models import User
from app.modules.voice import service as voice_service

router = APIRouter(prefix="/chat", tags=["chat"])


def _out(o: orchestrator.Outcome) -> dict:
    return {
        "conversation_id": o.conversation.id,
        "user_message": service.message_out(o.user_message),
        "assistant_message": service.message_out(o.assistant_message),
        "audio": o.audio,
    }


@router.post("/messages", response_model=ChatOut, dependencies=[Depends(rate_limit("chat_messages", 30, 60))])
async def send_message(body: ChatIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    outcome = await orchestrator.handle(
        session, user, body.text, input_mode="text", language_hint=body.language,
        conversation_id=body.conversation_id, want_audio=body.want_audio,
    )
    return _out(outcome)


@router.post("/voice", response_model=VoiceChatOut, dependencies=[Depends(rate_limit("chat_voice", 10, 60))])
async def send_voice(
    audio: UploadFile = File(...),
    conversation_id: uuid.UUID | None = Form(None),
    language: Language | None = Form(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    data = await audio.read(voice_service.AUDIO_MAX_BYTES + 1)
    await audio.close()
    heard = await voice_service.transcribe_upload(data, audio.content_type, language or user.preferred_language)
    outcome = await orchestrator.handle(
        session, user, heard.text[:2000], input_mode="voice", language_hint=heard.language,
        conversation_id=conversation_id,
    )
    return {**_out(outcome), "transcript": heard.text, "detected_language": heard.language}


@router.get("/greeting", response_model=GreetingOut)
async def chat_greeting(
    request: Request, lang: str | None = None,
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db),
):
    return await service.greeting(session, user, resolve_language(request, lang, fallback=user.preferred_language))


@router.get("/conversations", response_model=ConversationPage)
async def list_conversations(
    limit: int = Query(default=30, ge=1, le=100), cursor: str | None = None,
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db),
):
    return await service.list_conversations(session, user, limit, cursor)


@router.get("/conversations/{conversation_id}/messages", response_model=MessagePage)
async def list_messages(
    conversation_id: uuid.UUID, limit: int = Query(default=30, ge=1, le=100), cursor: str | None = None,
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db),
):
    return await service.list_messages(session, user, conversation_id, limit, cursor)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> Response:
    await service.delete_conversation(session, user, conversation_id)
    return Response(status_code=204)
