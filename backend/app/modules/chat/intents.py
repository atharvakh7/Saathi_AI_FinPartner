"""Intent routing (spec §5.3 step 5): keyword rules in four languages first, LLM router when no rule
or several rules match.

Distress is checked first and wins over everything (safety: never left to the LLM alone).
"""

import logging
import re
from dataclasses import dataclass, field

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import llm_client
from app.ai.base import AIOutputError, AIUnavailable
from app.ai.prompts import fence, render
from app.modules.learn import term_detector

log = logging.getLogger(__name__)

INTENTS = (
    "general_finance", "jargon_explain", "scam_check", "scheme_query", "log_transaction", "goal_action",
    "budget_query", "smalltalk", "distress", "out_of_scope",
)


def _rx(*parts: str) -> re.Pattern:
    return re.compile("|".join(parts), re.IGNORECASE | re.UNICODE)


# Self-harm / suicide / extreme despair, in en, romanized hi/mr, hi, mr, ta.
DISTRESS = _rx(
    r"\b(suicide|kill myself|end (my|this) life|want to die|wanna die|no reason to live|self[- ]?harm|"
    r"hurt myself|better off dead)\b",
    r"\b(mar jaana|mar jana|marna chahta|marna chahti|jaan de dunga|jaan de dungi|aatmahatya|atmahatya|"
    r"khudkushi|jeena nahi|jina nahi)\b",
    r"आत्महत्या|मर जाना|मरना चाहता|मरना चाहती|जान दे दूंगा|जान दे दूँगा|जान दे दूंगी|ख़ुदकुशी|खुदकुशी|जीना नहीं",
    r"जीव द्यायचा|मरून जावं|मरायचं आहे|जगायचं नाही",
    r"தற்கொலை|சாக வேண்டும்|சாகப் போகிறேன்|உயிரை மாய்த்து",
)

_URL = re.compile(r"https?://|www\.|\b[a-z0-9-]+\.(com|in|xyz|top|ly|co|net|org|info|link|site|online)\b", re.I)
SCAM = _rx(
    r"\b(scam|fraud|fake|genuine|is (this|it) (real|true|safe|legit)|spam)\b",
    r"\b(sach hai|sahi hai kya|asli hai|nakli|dhokha|farzi|froud)\b",
    r"क्या यह सच है|सच है क्या|फ्रॉड|धोखा|फर्जी|नकली|स्कैम",
    r"खरं आहे का|फसवणूक|बनावट",
    r"மோசடி|உண்மையா|போலி",
)
SCHEME = _rx(
    r"\b(schemes?|yojana|yojna|subsid(y|ies)|pension|government benefit|sarkari)\b",
    r"योजना|सब्सिडी|पेंशन|पेन्शन|अनुदान",
    r"திட்டம்|ஓய்வூதியம்|மானியம்",
)
_MONEY_VERB = _rx(
    r"\b(earned|spent|sold|bought|paid|received|got paid|kamaye|kamaya|kharcha|kharch kiya|becha|bechi|kharida|"
    r"diye|mile|mila|bharle|vikla|vikle|ghetla)\b",
    r"कमाए|कमाया|खर्च|बेचा|बेची|खरीदा|दिए|मिले|मिला|भरा|विकला|विकले|घेतला|भरले|मिळाले",
    r"செலவு|சம்பாதித்தேன்|விற்றேன்|வாங்கினேன்|கொடுத்தேன்|கிடைத்தது",
)
GOAL = _rx(
    r"\b(goal|save for|saving for|bachat karni|lakshya)\b",
    r"लक्ष्य|के लिए बचत|ध्येय|साठी बचत",
    r"இலக்கு|சேமிக்க வேண்டும்",
)
BUDGET = _rx(
    r"\b(budget|my plan|savings target|emergency fund|how much (can|should) i (save|spend))\b",
    r"बजट|बचत लक्ष्य|आपातकालीन|आपत्कालीन निधी|अंदाजपत्रक",
    r"பட்ஜெட்|அவசர நிதி",
)
_QUESTION = _rx(
    r"\b(what is|what's|what are|meaning of|means|define|explain)\b",
    r"\b(kya hai|kya hota|kya hoti|kya hote|matlab|mhanje kay|mhanje)\b",
    r"क्या है|क्या होता|क्या होती|मतलब|म्हणजे काय|म्हणजे",
    r"என்றால் என்ன|என்ன அர்த்தம்",
)

_OWN = _rx(
    r"\b(my|mine|mera|meri|mere|maza|majha|majhi|maji|mazi)\b",
    r"मेरा|मेरी|मेरे|माझा|माझी|माझे|माझं|என்\s|எனது",
)


@dataclass
class Routed:
    intent: str
    entities: dict = field(default_factory=dict)
    source: str = "rules"  # rules | llm | fallback


def rule_matches(text: str, language: str) -> tuple[list[str], dict]:
    """All rule intents that match, plus entities found on the way (e.g. the glossary term).

    Glossary matching needs the term detector loaded (`term_detector.detect` once per request)."""
    found: list[str] = []
    entities: dict = {}
    if _URL.search(text) or SCAM.search(text):
        found.append("scam_check")
    if _QUESTION.search(text) and not _OWN.search(text):  # "what is MY budget" is about their data
        spans = term_detector.find(text, language)
        if spans:
            found.append("jargon_explain")
            entities["term_slug"] = spans[0].slug
    if SCHEME.search(text):
        found.append("scheme_query")
    if _MONEY_VERB.search(text):  # without an amount the flow asks for it
        found.append("log_transaction")
    if GOAL.search(text):
        found.append("goal_action")
    if BUDGET.search(text):
        found.append("budget_query")
    return found, entities


class _RouterOut(BaseModel):
    intent: str
    entities: dict = Field(default_factory=dict)


async def route(session: AsyncSession, text: str, language: str) -> Routed:
    if DISTRESS.search(text):
        return Routed("distress")
    await term_detector.detect(session, "", language)  # make sure the glossary patterns are loaded
    found, entities = rule_matches(text, language)
    if len(found) == 1:
        return Routed(found[0], entities)
    try:
        result = await llm_client.chat_completion(
            [{"role": "user", "content": render("intent_router", message=fence(text))}],
            json_schema=_RouterOut, temperature=0.0, max_tokens=150,
        )
        out = result.data
        if out.intent in INTENTS:
            # keep rule-found entities (e.g. the glossary slug) unless the LLM gave its own
            return Routed(out.intent, {**entities, **{k: v for k, v in out.entities.items() if v not in (None, "")}}, "llm")
        log.warning("router returned unknown intent", extra={"intent": out.intent})
    except AIOutputError as exc:
        log.warning("intent router output unusable", extra={"error": repr(exc)})
    except AIUnavailable:
        raise
    # Router unusable: first rule match, else a general answer.
    return Routed(found[0] if found else "general_finance", entities, "fallback")
