"""Fraud Shield rules engine (spec §5.7 steps 2–4, 6–7). Pure functions apart from `load_patterns`.

Matching notes (ASSUMPTIONS step 14):
- Keywords match the lowercased, normalized text. Latin keywords need a word start before them, and
  short ones (≤ 4 letters: "rbi", "cvv", "trai") also a word end after them, so "train" is not "trai"
  but "prizes" still matches "prize". Devanagari/Tamil keywords match anywhere (endings attach).
- Links: explicit http(s):// or www. links, plus bare domains with a common TLD ("paytm-kyc.in/x").
- `requires_codes`: any-of codes that must also match ("R09" needs R02 or R03); "!R02" means R02 must
  NOT match (used by the S01 negative rule).
"""

import hashlib
import ipaddress
import json
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client
from app.modules.fraud.models import FraudPattern

log = logging.getLogger(__name__)

PATTERNS_CACHE_KEY = "fraud:patterns"
PATTERNS_CACHE_SEC = 600  # spec: cached in Redis 10 min
MAX_REASONS = 6
VERDICT_BANDS = ((70, "dangerous"), (35, "suspicious"), (0, "safe"))
# (Suggested, ASSUMPTIONS step 14) Signs that are fraud on their own by RBI/NPCI guidance: asking for
# OTP/PIN/IDs, an APK, an advance fee, remote access, UPI pay-to-receive. With at least one other sign
# the score is raised to the "dangerous" floor. Needed because the spec's weights assume the ML
# classifier adds to the score, and the classifier is off by default.
CRITICAL_CODES = frozenset({"R02", "R05", "R06", "R11", "R13"})
CRITICAL_FLOOR = 70

_TLDS = (
    "com|in|net|org|info|xyz|top|co|io|me|online|site|live|app|ly|gd|at|link|club|shop|biz|cc|tk|ml|ga|cf|gq|pw"
    "|ru|cn|vip|win|icu|buzz|lol|today|store|tech|pro|us|uk|website|space|fun|click|loan|work|money|gy"
)
_URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s<>\"'()]+"
    rf"|(?<![\w@.-])(?:[a-z0-9-]+\.)+(?:{_TLDS})\b(?::\d+)?(?:/[^\s<>\"'()]*)?",
    re.IGNORECASE,
)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?([6-9]\d{9})(?!\d)")
_LONG_DIGITS_RE = re.compile(r"\d{6,}")
_INDIC = re.compile(r"[ऀ-ॿ஀-௿]")


# --- Normalization -----------------------------------------------------------------

@dataclass(frozen=True)
class Normalized:
    text: str          # NFKC, whitespace collapsed, Indic digits -> 0-9
    lower: str
    urls: list[str]
    hosts: list[str]   # lowercase, without "www.", in order of appearance, unique
    phones: list[str]  # 10-digit mobiles
    has_http: bool     # at least one explicit http:// (non-HTTPS) link


def _ascii_digits(text: str) -> str:
    return "".join(str(unicodedata.digit(ch)) if ch.isdigit() and not ch.isascii() else ch for ch in text)


def _host(url: str) -> str | None:
    url = url.rstrip(".,;:!?'\"")
    try:
        host = urlsplit(url if "://" in url else f"http://{url}").hostname
    except ValueError:
        return None
    if not host:
        return None
    return host[4:] if host.startswith("www.") else host


def normalize(raw: str) -> Normalized:
    text = " ".join(_ascii_digits(unicodedata.normalize("NFKC", raw)).split())
    urls = [u.rstrip(".,;:!?'\"") for u in _URL_RE.findall(text)]
    hosts: list[str] = []
    for u in urls:
        h = _host(u)
        if h and h not in hosts:
            hosts.append(h)
    phones = list(dict.fromkeys(_PHONE_RE.findall(text)))
    has_http = any(u.lower().startswith("http://") for u in urls)
    return Normalized(text, text.lower(), urls, hosts, phones, has_http)


def text_hash(n: Normalized) -> str:
    return hashlib.sha256(n.lower.encode("utf-8")).hexdigest()


def make_snippet(n: Normalized, length: int = 40) -> str:
    """First 40 characters + "…", with digit runs of 6+ masked (spec §6.1 fraud_checks.snippet)."""
    masked = _LONG_DIGITS_RE.sub("••••", n.text)
    return masked if len(masked) <= length else masked[:length].rstrip() + "…"


# --- Patterns ----------------------------------------------------------------------

@dataclass(frozen=True)
class Pattern:
    code: str
    pattern_type: str
    patterns: list[str]
    weight: int
    requires_codes: list[str] | None
    reason_key: str | None
    reason_title_en: str | None
    reason_text_en: str | None


async def load_patterns(session: AsyncSession) -> list[Pattern]:
    """Active patterns, from the Redis cache (10 min) or the database."""
    try:
        cached = await redis_client.get(PATTERNS_CACHE_KEY)
        if cached:
            return [Pattern(**p) for p in json.loads(cached)]
    except RedisError as exc:
        log.warning("fraud pattern cache unavailable", extra={"error": str(exc)})
    rows = (await session.execute(select(FraudPattern).where(FraudPattern.is_active).order_by(FraudPattern.code))).scalars()
    patterns = [
        Pattern(r.code, r.pattern_type, list(r.patterns), r.weight, r.requires_codes, r.reason_key,
                r.reason_title_en, r.reason_text_en)
        for r in rows
    ]
    try:
        await redis_client.set(PATTERNS_CACHE_KEY, json.dumps([p.__dict__ for p in patterns]), ex=PATTERNS_CACHE_SEC)
    except RedisError:
        pass
    return patterns


async def invalidate_patterns() -> None:
    """Admin writes (step 18) call this so changes apply immediately."""
    try:
        await redis_client.delete(PATTERNS_CACHE_KEY)
    except RedisError:
        pass


_compiled: dict[tuple, re.Pattern] = {}


def _regex(source: str) -> re.Pattern:
    key = ("re", source)
    if key not in _compiled:
        _compiled[key] = re.compile(source, re.IGNORECASE | re.UNICODE)
    return _compiled[key]


def _keyword_regex(keyword: str) -> re.Pattern:
    key = ("kw", keyword)
    if key not in _compiled:
        kw = keyword.lower()
        body = re.escape(kw).replace(r"\ ", r"\s+")
        if _INDIC.search(kw):
            source = body
        else:
            start = r"(?<![a-z0-9])"
            end = r"(?![a-z0-9])" if len(kw) <= 4 else ""
            source = start + body + end
        _compiled[key] = re.compile(source, re.UNICODE)
    return _compiled[key]


def _is_official(host: str, domain: str) -> bool:
    return host == domain or host.endswith("." + domain)


def _brand_lookalike(host: str, token: str, official: str) -> bool:
    if _is_official(host, official):
        return False
    if len(token) >= 5:
        return token in host
    return re.search(rf"(?:^|[.-]){re.escape(token)}", host) is not None


def _suspicious_link(n: Normalized, entries: list[str]) -> bool:
    for host in n.hosts:
        if "@ip_host" in entries:
            try:
                ipaddress.ip_address(host)
                return True
            except ValueError:
                pass
        if "@punycode" in entries and ("xn--" in host or not host.isascii()):
            return True
        if any(not e.startswith("@") and _is_official(host, e) for e in entries):
            return True
    return "@non_https" in entries and n.has_http


def _matches(p: Pattern, n: Normalized) -> bool:
    if p.pattern_type == "keyword":
        return any(_keyword_regex(k).search(n.lower) for k in p.patterns)
    if p.pattern_type == "regex":
        return any(_regex(r).search(n.text) for r in p.patterns)
    if p.pattern_type == "url":
        if any(":" in e and not e.startswith("@") for e in p.patterns):  # brand_token:official_domain
            pairs = [e.split(":", 1) for e in p.patterns]
            return any(_brand_lookalike(h, tok, off) for h in n.hosts for tok, off in pairs)
        return _suspicious_link(n, p.patterns)
    if p.pattern_type == "negative":  # every link is an official domain
        return bool(n.hosts) and all(any(_is_official(h, d) for d in p.patterns) for h in n.hosts)
    return False


# --- Evaluation --------------------------------------------------------------------

@dataclass
class RuleResult:
    matched: list[Pattern] = field(default_factory=list)
    rule_score: int = 0

    @property
    def codes(self) -> list[str]:
        return sorted(p.code for p in self.matched if p.weight > 0)


def evaluate(patterns: list[Pattern], n: Normalized) -> RuleResult:
    base = {p.code for p in patterns if not p.requires_codes and _matches(p, n)}
    matched = []
    for p in patterns:
        if not p.requires_codes:
            if p.code in base:
                matched.append(p)
            continue
        required = [c for c in p.requires_codes if not c.startswith("!")]
        forbidden = [c[1:] for c in p.requires_codes if c.startswith("!")]
        if required and not any(c in base for c in required):
            continue
        if any(c in base for c in forbidden):
            continue
        if _matches(p, n):
            matched.append(p)
    total = sum(p.weight for p in matched)  # each rule counts once, however often it matches
    positive = {p.code for p in matched if p.weight > 0}
    if positive & CRITICAL_CODES and len(positive) >= 2:
        total = max(total, CRITICAL_FLOOR)
    return RuleResult(matched, max(0, min(100, total)))


def final_score(rule_score: int, classifier_score: float | None) -> int:
    if classifier_score is None:
        return rule_score
    blended = 0.6 * rule_score + 0.4 * 100 * classifier_score
    return max(0, min(100, round(max(rule_score, blended))))


def verdict_for(score: int) -> str:
    return next(v for floor, v in VERDICT_BANDS if score >= floor)


def reasons(result: RuleResult) -> list[dict]:
    """Up to 6 reasons, heaviest first, one per reason_key (R01 and R01b share one)."""
    out, seen = [], set()
    for p in sorted(result.matched, key=lambda p: (-p.weight, p.code)):
        if p.weight <= 0 or not p.reason_key or p.reason_key in seen:
            continue
        seen.add(p.reason_key)
        out.append({"code": p.code, "key": p.reason_key, "title": p.reason_title_en, "text": p.reason_text_en})
    return out[:MAX_REASONS]
