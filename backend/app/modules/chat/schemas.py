"""Chat DTOs (spec §7.3 ChatMessageDTO, §7.4 /chat/*)."""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

Language = Literal["en", "hi", "mr", "ta"]


class ChatIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conversation_id: uuid.UUID | None = None
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    language: Language | None = None
    want_audio: bool = False


class TermSpanOut(BaseModel):
    slug: str
    surface: str
    start: int
    end: int


class CardOut(BaseModel):
    type: Literal["term", "fraud_result", "scheme_list", "budget_summary", "goal", "transaction_draft"]
    payload: dict


class ChatMessageOut(BaseModel):
    id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    language: str | None
    input_mode: str
    intent: str | None
    highlighted_terms: list[TermSpanOut]
    cards: list[CardOut]
    suggested_replies: list[str]
    mascot_pose: str | None
    created_at: datetime


class AudioOut(BaseModel):
    url: str
    mime: Literal["audio/wav"] = "audio/wav"
    expires_in_sec: int


class ChatOut(BaseModel):
    conversation_id: uuid.UUID
    user_message: ChatMessageOut
    assistant_message: ChatMessageOut
    audio: AudioOut | None


class VoiceChatOut(ChatOut):
    transcript: str
    detected_language: str


class ConversationItem(BaseModel):
    id: uuid.UUID
    title: str | None
    channel: str
    last_message_at: datetime


class ConversationPage(BaseModel):
    items: list[ConversationItem]
    next_cursor: str | None


class MessagePage(BaseModel):
    items: list[ChatMessageOut]
    next_cursor: str | None


class GreetingOut(BaseModel):
    text: str
    mascot_pose: str = "wave"
    suggested_replies: list[str]
