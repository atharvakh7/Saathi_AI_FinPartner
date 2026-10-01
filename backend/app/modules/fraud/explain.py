"""Summary + advice for a fraud check (spec §5.7 step 8).

The verdict is decided by the rules; the LLM (fraud_explain.md) only explains it in the user's
language. The message is fenced as untrusted data. The reply is rejected (-> template text) if it
repeats a link or phone number from the message, tells the user to click/call/pay, or is too long.
"""

import logging
import re

from pydantic import BaseModel, Field

from app.ai import llm_client
from app.ai.base import AIOutputError, AIUnavailable
from app.ai.prompts import fence, language_name, render
from app.modules.fraud.rules import Normalized

log = logging.getLogger(__name__)

PROMPT_MESSAGE_CHARS = 2000
SUMMARY_MAX = 300
ADVICE_MAX = 400


class _Explanation(BaseModel):
    summary: str = Field(min_length=5)
    advice: str = Field(min_length=5)


# Template fallback per language and verdict (summary, advice).
TEMPLATES: dict[str, dict[str, tuple[str, str]]] = {
    "en": {
        "dangerous": ("This message shows strong signs of a scam.",
                      "Do not click any link, call back, pay, or share any OTP or PIN. Block the sender."),
        "suspicious": ("This message has some warning signs of a scam.",
                       "Don't act in a hurry. Check directly with the official app, website or branch first, "
                       "and never share your OTP or PIN."),
        "safe": ("We found no common scam signs in this message.",
                 "Still, never share your OTP, PIN or passwords with anyone."),
    },
    "hi": {
        "dangerous": ("इस संदेश में धोखाधड़ी के साफ़ संकेत हैं।",
                      "किसी लिंक पर क्लिक न करें, वापस कॉल न करें, पैसे न भेजें और OTP या PIN किसी को न बताएं। "
                      "भेजने वाले को ब्लॉक करें।"),
        "suspicious": ("इस संदेश में धोखाधड़ी के कुछ संकेत हैं।",
                       "जल्दबाज़ी न करें। कुछ भी करने से पहले आधिकारिक ऐप, वेबसाइट या शाखा से सीधे पता करें, "
                       "और OTP या PIN कभी न बताएं।"),
        "safe": ("इस संदेश में धोखाधड़ी के आम संकेत नहीं मिले।",
                 "फिर भी, अपना OTP, PIN या पासवर्ड किसी को न बताएं।"),
    },
    "mr": {
        "dangerous": ("या संदेशात फसवणुकीची स्पष्ट चिन्हे आहेत.",
                      "कोणत्याही लिंकवर क्लिक करू नका, परत कॉल करू नका, पैसे पाठवू नका आणि OTP किंवा PIN कोणालाही "
                      "सांगू नका. पाठवणाऱ्याला ब्लॉक करा."),
        "suspicious": ("या संदेशात फसवणुकीची काही चिन्हे आहेत.",
                       "घाई करू नका. काहीही करण्यापूर्वी अधिकृत ॲप, वेबसाइट किंवा शाखेत थेट खात्री करा, आणि OTP "
                       "किंवा PIN कधीही सांगू नका."),
        "safe": ("या संदेशात फसवणुकीची नेहमीची चिन्हे आढळली नाहीत.",
                 "तरीही, तुमचा OTP, PIN किंवा पासवर्ड कोणालाही सांगू नका."),
    },
    "ta": {
        "dangerous": ("இந்தச் செய்தியில் மோசடிக்கான தெளிவான அறிகுறிகள் உள்ளன.",
                      "எந்த இணைப்பையும் திறக்காதீர்கள், திரும்ப அழைக்காதீர்கள், பணம் அனுப்பாதீர்கள், OTP அல்லது "
                      "PIN-ஐ யாரிடமும் சொல்லாதீர்கள். அனுப்பியவரைத் தடுக்கவும்."),
        "suspicious": ("இந்தச் செய்தியில் மோசடிக்கான சில அறிகுறிகள் உள்ளன.",
                       "அவசரப்பட வேண்டாம். எதையும் செய்வதற்கு முன் அதிகாரப்பூர்வ செயலி, இணையதளம் அல்லது கிளையில் "
                       "நேரடியாகச் சரிபார்க்கவும். OTP அல்லது PIN-ஐ ஒருபோதும் பகிர வேண்டாம்."),
        "safe": ("இந்தச் செய்தியில் பொதுவான மோசடி அறிகுறிகள் எதுவும் இல்லை.",
                 "இருந்தாலும், உங்கள் OTP, PIN அல்லது கடவுச்சொல்லை யாரிடமும் பகிர வேண்டாம்."),
    },
}

# English instructions that must never appear in advice (the LLM writes other languages too; the
# link/number check below covers those).
_UNSAFE_ADVICE = re.compile(
    r"\b(click (on )?(the|this) link|call (the|this) number|pay the fee|share (the|your) (otp|pin)|"
    r"install the app|reply to (the|this) message)\b",
    re.IGNORECASE,
)


def template(verdict: str, language: str) -> dict[str, str]:
    summary, advice = TEMPLATES.get(language, TEMPLATES["en"])[verdict]
    return {"summary": summary, "advice": advice}


def _problem(out: _Explanation, n: Normalized) -> str | None:
    text = f"{out.summary}\n{out.advice}"
    if len(out.summary) > SUMMARY_MAX or len(out.advice) > ADVICE_MAX:
        return "too long"
    lowered = text.lower()
    if "http" in lowered or any(h in lowered for h in n.hosts):
        return "repeats a link"
    digits = re.sub(r"\D", "", text)
    if any(p in digits for p in n.phones) or re.search(r"\d{8,}", re.sub(r"[\s-]", "", text)):
        return "repeats a number"
    if _UNSAFE_ADVICE.search(out.advice) and not re.search(r"\b(do not|don't|never|avoid)\b", out.advice, re.I):
        return "unsafe advice"
    return None


async def explain(n: Normalized, verdict: str, risk_score: int, reasons: list[dict], language: str) -> dict[str, str]:
    """Returns {"summary", "advice"} in `language`; never raises."""
    reason_lines = "\n".join(f"- {r['title']}: {r['text']}" for r in reasons) or "- No common scam signs found."
    prompt = render(
        "fraud_explain", verdict=verdict, risk_score=risk_score, reasons=reason_lines,
        language_name=language_name(language), message=fence(n.text[:PROMPT_MESSAGE_CHARS], "message"),
    )
    try:
        result = await llm_client.chat_completion(
            [{"role": "user", "content": prompt}], json_schema=_Explanation, temperature=0.2, max_tokens=400,
            timeout=60,
        )
    except (AIUnavailable, AIOutputError) as exc:
        log.warning("fraud explanation fell back to template", extra={"error": repr(exc)})
        return template(verdict, language)
    problem = _problem(result.data, n)
    if problem:
        log.warning("fraud explanation rejected", extra={"problem": problem})
        return template(verdict, language)
    return {"summary": result.data.summary.strip(), "advice": result.data.advice.strip()}
