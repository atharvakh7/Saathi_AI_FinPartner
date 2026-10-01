"""/chat/transcribe and /chat/tts (spec §7.4). /chat/voice (speech in, reply out) is in the chat
module (step 16) and reuses voice.service."""

from typing import Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from app.ai.base import AIUnavailable
from app.core.errors import AppError
from app.core.rate_limit import rate_limit
from app.core.security import get_current_user
from app.core.storage import TTS_URL_TTL_SEC
from app.modules.users.models import User
from app.modules.voice import service

router = APIRouter(prefix="/chat", tags=["voice"])

Language = Literal["en", "hi", "mr", "ta"]


class TranscribeOut(BaseModel):
    text: str
    language: str
    confidence: float


class TtsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=1000)
    language: Language | None = None  # null -> the user's preferred language


class TtsOut(BaseModel):
    url: str
    mime: Literal["audio/wav"] = "audio/wav"
    expires_in_sec: int


class TtsNoVoiceOut(BaseModel):
    url: None = None
    reason: Literal["no_voice_for_language"] = "no_voice_for_language"  # the app speaks it on-device (A8)


@router.post("/transcribe", response_model=TranscribeOut, dependencies=[Depends(rate_limit("chat_transcribe", 20, 60))])
async def transcribe(
    audio: UploadFile = File(...),
    language: Language | None = Form(None),
    user: User = Depends(get_current_user),
):
    data = await audio.read(service.AUDIO_MAX_BYTES + 1)
    await audio.close()
    # No hint: the user's language is the prior (Whisper small mislabels some Marathi speech).
    result = await service.transcribe_upload(data, audio.content_type, language or user.preferred_language)
    return TranscribeOut(text=result.text, language=result.language, confidence=result.confidence)


@router.post("/tts", response_model=TtsOut | TtsNoVoiceOut, dependencies=[Depends(rate_limit("chat_tts", 30, 60))])
async def text_to_speech(body: TtsIn, user: User = Depends(get_current_user)):
    try:
        url = await service.speech_url(body.text, body.language or user.preferred_language)
    except AIUnavailable as exc:
        raise AppError("UPSTREAM_AI_UNAVAILABLE") from exc
    if url is None:
        return TtsNoVoiceOut()
    return TtsOut(url=url, expires_in_sec=TTS_URL_TTL_SEC)
