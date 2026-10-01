"""Fraud Shield: analyze, history, reports (spec §5.7, §7.4 /fraud/*).

`analyze_text` is also what the chat orchestrator calls for the scam_check intent (step 16).
Screenshot bytes are only held in memory for OCR and never stored (spec §5.7 step 1).
"""

import logging
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Text, and_, delete, func, or_, select
from sqlalchemy.dialects.postgresql import array, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import classifier, ocr
from app.ai.base import AIUnavailable
from app.core.errors import AppError
from app.core.pagination import after_cursor, decode_cursor, encode_cursor
from app.modules.fraud import explain, rules
from app.modules.fraud.models import FraudCheck, FraudReport
from app.modules.fraud.schemas import FraudCheckListItem, FraudCheckOut, FraudCheckPage, ReasonOut
from app.modules.users.models import User

log = logging.getLogger(__name__)

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
IMAGE_MAX_BYTES = 5 * 1024 * 1024
OCR_MIN_CHARS = 10
TEXT_MAX_CHARS = 5000


# --- Analyze -----------------------------------------------------------------------

async def analyze_text(
    session: AsyncSession, user: User, raw_text: str, *, source_app: str = "other", input_type: str = "text",
    language: str | None = None,
) -> FraudCheckOut:
    language = language or user.preferred_language
    n = rules.normalize(raw_text[:TEXT_MAX_CHARS])
    result = rules.evaluate(await rules.load_patterns(session), n)
    p_scam = await classifier.scam_probability(n.text)
    score = rules.final_score(result.rule_score, p_scam)
    verdict = rules.verdict_for(score)
    reasons = rules.reasons(result)
    words = await explain.explain(n, verdict, score, reasons, language)

    check = FraudCheck(
        user_id=user.id, input_type=input_type, source_app=source_app, extracted_text=n.text,
        text_hash=rules.text_hash(n), snippet=rules.make_snippet(n), risk_score=score, verdict=verdict,
        matched_rules=[{"code": p.code, "weight": p.weight} for p in result.matched],
        classifier_score=Decimal(str(round(p_scam, 3))) if p_scam is not None else None,
        explanation={**words, "reasons": reasons}, language=language, extracted_domains=n.hosts or None,
    )
    session.add(check)
    await session.commit()
    await session.refresh(check)  # created_at is set by the database
    log.info("fraud check", extra={"verdict": verdict, "risk_score": score, "codes": result.codes})
    return await _out(session, user, check)


async def analyze_image(
    session: AsyncSession, user: User, image: bytes, content_type: str | None, *, source_app: str,
    language: str | None,
) -> FraudCheckOut:
    if len(image) > IMAGE_MAX_BYTES:
        raise AppError("PAYLOAD_TOO_LARGE")
    if (content_type or "").lower() not in IMAGE_TYPES:
        raise AppError("UNSUPPORTED_MEDIA_TYPE")
    try:
        extracted = await ocr.extract_text(image)
    except ValueError as exc:  # not actually an image
        raise AppError("UNSUPPORTED_MEDIA_TYPE") from exc
    except AIUnavailable as exc:
        raise AppError("UPSTREAM_AI_UNAVAILABLE") from exc
    finally:
        del image  # never stored (spec §5.7 step 1)
    if len("".join(extracted.split())) < OCR_MIN_CHARS:
        raise AppError("OCR_NO_TEXT")
    return await analyze_text(session, user, extracted, source_app=source_app, input_type="screenshot",
                              language=language)


# --- Reads -------------------------------------------------------------------------

async def similar_reports_count(session: AsyncSession, check: FraudCheck) -> int:
    """Reports by other users of the same text, or of a near-duplicate: the same set of matched rule
    codes and a shared link domain (spec §5.7 step 9)."""
    codes = sorted(r["code"] for r in check.matched_rules if r["weight"] > 0)
    same = FraudReport.text_hash == check.text_hash
    if codes and check.extracted_domains:
        near = and_(
            FraudReport.matched_codes == codes,
            FraudReport.extracted_domains.has_any(array(list(check.extracted_domains), type_=Text)),
        )
        same = or_(same, near)
    return (
        await session.execute(
            select(func.count(func.distinct(FraudReport.user_id))).where(same, FraudReport.user_id != check.user_id)
        )
    ).scalar_one()


async def _reported(session: AsyncSession, user: User, check: FraudCheck) -> bool:
    return (
        await session.execute(
            select(FraudReport.id).where(FraudReport.user_id == user.id, FraudReport.text_hash == check.text_hash)
        )
    ).first() is not None


async def _out(session: AsyncSession, user: User, check: FraudCheck) -> FraudCheckOut:
    ex = check.explanation
    return FraudCheckOut(
        id=check.id, input_type=check.input_type, source_app=check.source_app, snippet=check.snippet,
        risk_score=check.risk_score, verdict=check.verdict, summary=ex["summary"], advice=ex["advice"],
        reasons=[ReasonOut(**r) for r in ex.get("reasons", [])],
        similar_reports_count=await similar_reports_count(session, check),
        reported=await _reported(session, user, check),
        language=check.language, created_at=check.created_at,
    )


async def _own_check(session: AsyncSession, user: User, check_id: uuid.UUID) -> FraudCheck:
    check = await session.get(FraudCheck, check_id)
    if check is None or check.user_id != user.id:
        raise AppError("NOT_FOUND")
    return check


async def get_check(session: AsyncSession, user: User, check_id: uuid.UUID) -> FraudCheckOut:
    return await _out(session, user, await _own_check(session, user, check_id))


async def list_checks(session: AsyncSession, user: User, limit: int, cursor: str | None) -> FraudCheckPage:
    stmt = select(FraudCheck).where(FraudCheck.user_id == user.id)
    if cursor:
        stmt = stmt.where(after_cursor([FraudCheck.created_at, FraudCheck.id],
                                       decode_cursor(cursor, [datetime.fromisoformat, uuid.UUID])))
    rows = list((await session.execute(
        stmt.order_by(FraudCheck.created_at.desc(), FraudCheck.id.desc()).limit(limit + 1)
    )).scalars())
    page = rows[:limit]
    return FraudCheckPage(
        items=[FraudCheckListItem(id=c.id, snippet=c.snippet, source_app=c.source_app, input_type=c.input_type,
                                  verdict=c.verdict, risk_score=c.risk_score, created_at=c.created_at) for c in page],
        next_cursor=encode_cursor([page[-1].created_at, page[-1].id]) if len(rows) > limit else None,
    )


# --- Writes ------------------------------------------------------------------------

async def delete_check(session: AsyncSession, user: User, check_id: uuid.UUID) -> None:
    """Reports made from this check stay (fraud_check_id -> NULL); they hold no message text."""
    await _own_check(session, user, check_id)
    await session.execute(delete(FraudCheck).where(FraudCheck.id == check_id))
    await session.commit()


async def report_check(session: AsyncSession, user: User, check_id: uuid.UUID) -> bool:
    check = await _own_check(session, user, check_id)
    await session.execute(
        insert(FraudReport)
        .values(user_id=user.id, fraud_check_id=check.id, text_hash=check.text_hash,
                matched_codes=sorted(r["code"] for r in check.matched_rules if r["weight"] > 0),
                extracted_domains=check.extracted_domains)
        .on_conflict_do_nothing(index_elements=["user_id", "text_hash"])  # idempotent
    )
    await session.commit()
    return True
