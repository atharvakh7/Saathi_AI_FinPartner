"""Detect en / hi / mr / ta in user text (spec §3.2, §5.3 step 2).

1. Script: Tamil letters -> ta. Devanagari -> hi or mr (lingua, restricted to those two).
2. Latin script: users often type Hindi/Marathi/Tamil in English letters ("SIP kya hota hai").
   Common romanized function words decide; otherwise English.
The orchestrator applies the spec's rules on top (confidence < 0.6 -> preferred language;
Devanagari + preferred hi/mr -> preferred).
"""

import re
import threading
from dataclasses import dataclass

from app.core.enums import LANGUAGES

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_TAMIL = re.compile(r"[஀-௿]")
_LATIN = re.compile(r"[A-Za-z]")
_WORD = re.compile(r"[a-z]+")

# Frequent romanized words that are rarely English. Kept short and distinctive on purpose.
_ROMANIZED: dict[str, set[str]] = {
    "hi": {
        "kya", "hai", "hain", "hota", "hoti", "kaise", "kaisa", "kaisi", "mera", "meri", "mere", "mujhe", "kitna",
        "kitne", "kitni", "nahi", "nahin", "karna", "karun", "karoon", "aap", "apna", "apni", "chahiye", "batao",
        "bataiye", "kyun", "kyon", "lekin", "aur", "mein", "hoga", "tha", "thi", "raha", "rahi", "yeh", "kal", "aaj",
        "paisa", "paise", "kharcha", "bachat", "kamai", "karz", "kar", "ko", "se", "ki", "ka", "ke", "ho", "gaya",
    },
    "mr": {
        "aahe", "ahe", "kay", "kasa", "kashi", "kase", "mala", "tumhi", "tumhala", "tumcha", "majha", "majhi",
        "maza", "mazi", "kiti", "sanga", "sangaa", "kuthe", "hoil", "pahije", "zala", "jhala", "zali", "karaycha",
        "kara", "ata", "aata", "nahi", "ani", "pan", "mhanje", "hota", "hoti", "paise", "kharch", "bachat",
    },
    "ta": {
        "enna", "epdi", "eppadi", "panam", "irukku", "iruku", "enakku", "enaku", "naan", "neenga", "sollunga",
        "vendum", "venum", "evvalavu", "evlo", "illa", "illai", "seri", "romba", "enga", "ungal", "unga", "yenna",
        "pannanum", "panna", "selavu", "semippu", "kadan",
    },
}


@dataclass(frozen=True)
class Detection:
    language: str      # en | hi | mr | ta
    confidence: float  # 0..1
    script: str        # latin | devanagari | tamil | none


_detector = None
_detector_lock = threading.Lock()


def _hi_mr_detector():
    global _detector
    if _detector is None:
        with _detector_lock:
            if _detector is None:
                from lingua import Language, LanguageDetectorBuilder

                _detector = LanguageDetectorBuilder.from_languages(Language.HINDI, Language.MARATHI).build()
    return _detector


def _devanagari_language(text: str, fallback: str) -> Detection:
    from lingua import Language

    values = {v.language: v.value for v in _hi_mr_detector().compute_language_confidence_values(text)}
    hi, mr = values.get(Language.HINDI, 0.0), values.get(Language.MARATHI, 0.0)
    if abs(hi - mr) < 0.2 and fallback in ("hi", "mr"):
        return Detection(fallback, max(hi, mr), "devanagari")
    return Detection("hi" if hi >= mr else "mr", max(hi, mr), "devanagari")


def _latin_language(text: str) -> Detection:
    words = _WORD.findall(text.lower())
    if not words:
        return Detection("en", 0.5, "latin")
    scores = {lang: sum(w in vocab for w in words) for lang, vocab in _ROMANIZED.items()}
    best = max(scores, key=scores.get)
    hits = scores[best]
    ratio = hits / len(words)
    if hits >= 2 and ratio >= 0.2:
        # hi and mr share many words; only pick one when it clearly leads.
        runner_up = max(v for k, v in scores.items() if k != best)
        confidence = 0.8 if hits > runner_up else 0.55
        return Detection(best, confidence, "latin")
    confidence = 0.9 if len(words) >= 4 else 0.65
    return Detection("en", confidence, "latin")


def detect_text_language(text: str, fallback: str = "en") -> Detection:
    fallback = fallback if fallback in LANGUAGES else "en"
    tamil = len(_TAMIL.findall(text))
    deva = len(_DEVANAGARI.findall(text))
    latin = len(_LATIN.findall(text))
    if tamil == deva == latin == 0:
        return Detection(fallback, 0.0, "none")
    if tamil >= deva and tamil >= latin:
        return Detection("ta", 1.0, "tamil")
    if deva >= latin:
        return _devanagari_language(text, fallback)
    return _latin_language(text)
