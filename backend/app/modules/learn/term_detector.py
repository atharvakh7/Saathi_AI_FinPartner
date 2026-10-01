"""Find glossary terms in text (spec §5.8 "Term detection").

Per language, one regex alternation of: every term's `term_en`, the language's `term_local`, and
the term's `aliases`, longest first. Latin-script terms need word boundaries on both sides
("EMI" must not match inside "EMIT"). Devanagari/Tamil terms need a boundary only before them,
because Marathi and Tamil attach endings ("एसआयपीमध्ये", "எஸ்ஐபியில்").

Offsets are UTF-16 code units, the unit JavaScript strings use, so the app can slice the text
correctly even when it contains emoji.

The compiled patterns are cached in-process and rebuilt when the glossary changes: writers call
`invalidate()`, which bumps a Redis version so every API worker rebuilds on its next call.
"""

import logging
import re
import time
from dataclasses import dataclass

from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import LANGUAGES
from app.core.redis import redis_client
from app.modules.learn.models import GlossaryTerm, GlossaryTranslation

log = logging.getLogger(__name__)

MAX_TERMS = 5
VERSION_KEY = "glossary:version"
VERSION_CHECK_SEC = 10  # how often a worker asks Redis whether the glossary changed

_LETTER = r"\wऀ-ॿ஀-௿"  # \w misses Indic vowel signs, so include whole blocks
_INDIC = re.compile(r"[ऀ-ॿ஀-௿]")


@dataclass(frozen=True)
class Span:
    slug: str
    surface: str
    start: int  # UTF-16 offsets
    end: int


@dataclass
class _Compiled:
    pattern: re.Pattern | None
    groups: dict[str, str]  # regex group name -> slug


_cache: dict[str, _Compiled] = {}
_cache_version: str | None = None
_last_check = 0.0


def _term_regex(surface: str) -> str:
    body = re.escape(surface.strip()).replace(r"\ ", r"\s+")
    if _INDIC.search(surface):
        return rf"(?<![{_LETTER}]){body}"
    return rf"(?<![{_LETTER}]){body}(?![{_LETTER}])"


def _compile(surfaces: list[tuple[str, str]]) -> _Compiled:
    # Longest first so "health insurance" wins over "insurance"; dedupe identical surfaces.
    seen: dict[str, str] = {}
    for slug, surface in surfaces:
        key = surface.strip().lower()
        if len(key) >= 2 and key not in seen:
            seen[key] = slug
    if not seen:
        return _Compiled(None, {})
    parts, groups = [], {}
    for i, (surface, slug) in enumerate(sorted(seen.items(), key=lambda kv: -len(kv[0]))):
        name = f"t{i}"
        groups[name] = slug
        parts.append(f"(?P<{name}>{_term_regex(surface)})")
    return _Compiled(re.compile("|".join(parts), re.IGNORECASE | re.UNICODE), groups)


async def _current_version() -> str:
    try:
        return await redis_client.get(VERSION_KEY) or "0"
    except RedisError:
        return _cache_version or "0"


async def invalidate() -> None:
    """Call after any glossary or glossary-translation write."""
    global _cache_version
    _cache.clear()
    _cache_version = None
    try:
        await redis_client.incr(VERSION_KEY)
    except RedisError:
        pass


async def _build(session: AsyncSession) -> None:
    global _cache_version
    terms = list((await session.execute(select(GlossaryTerm).where(GlossaryTerm.is_active))).scalars())
    translations = list((await session.execute(select(GlossaryTranslation))).scalars())
    by_term_lang = {(t.term_id, t.language): t.term_local for t in translations}
    common = [(t.slug, t.term_en) for t in terms] + [(t.slug, a) for t in terms for a in (t.aliases or [])]
    _cache.clear()
    for lang in LANGUAGES:
        local = [(t.slug, by_term_lang[(t.id, lang)]) for t in terms if (t.id, lang) in by_term_lang]
        # Translations often add a gloss in brackets ("एसआईपी (नियमित निवेश)"); match the word itself.
        local += [(slug, re.split(r"\s*[(（]", s)[0]) for slug, s in local]
        _cache[lang] = _compile(common + local)
    _cache_version = await _current_version()


async def _ensure(session: AsyncSession) -> None:
    global _last_check
    now = time.monotonic()
    if _cache and now - _last_check < VERSION_CHECK_SEC:
        return
    _last_check = now
    if not _cache or await _current_version() != _cache_version:
        await _build(session)


def _utf16_len(s: str) -> int:
    return len(s.encode("utf-16-le")) // 2


def find(text: str, language: str) -> list[Span]:
    compiled = _cache.get(language if language in LANGUAGES else "en")
    if compiled is None or compiled.pattern is None or not text:
        return []
    spans: list[Span] = []
    seen_slugs: set[str] = set()
    for m in compiled.pattern.finditer(text):
        slug = compiled.groups[m.lastgroup]
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        start = _utf16_len(text[: m.start()])
        spans.append(Span(slug=slug, surface=m.group(0), start=start, end=start + _utf16_len(m.group(0))))
        if len(spans) >= MAX_TERMS:
            break
    return spans


async def detect(session: AsyncSession, text: str, language: str) -> list[Span]:
    await _ensure(session)
    return find(text, language)
