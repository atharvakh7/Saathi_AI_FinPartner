"""Request language resolution (spec §7: `lang` param, else Accept-Language, else default)."""

from fastapi import Request

from app.core.enums import LANGUAGES

DEFAULT_LANGUAGE = "en"


def resolve_language(request: Request, lang: str | None = None, fallback: str = DEFAULT_LANGUAGE) -> str:
    if lang in LANGUAGES:
        return lang
    header = request.headers.get("accept-language", "")
    # e.g. "hi", "hi-IN", "mr-IN,en;q=0.8" -> first supported primary tag
    for part in header.split(","):
        code = part.split(";")[0].strip().lower().split("-")[0]
        if code in LANGUAGES:
            return code
    return fallback if fallback in LANGUAGES else DEFAULT_LANGUAGE
