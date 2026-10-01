"""Idempotent seed of shared content (spec §6.3).

Run from backend/:
    .venv/Scripts/python -m app.seed.seed            # validate + upsert
    .venv/Scripts/python -m app.seed.seed --check    # validate only

Rows are upserted by slug/code, so re-running leaves counts unchanged. Seeded rows are
overwritten with the JSON content on every run; content edited through the admin API
should also be copied back into these files, or it will be reset by the next seed.
"""

import argparse
import asyncio
import json
import re
import sys
from datetime import date
from pathlib import Path

from sqlalchemy import String, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

import app.models_registry  # noqa: F401
from app.core.config import settings
from app.core.db import Base, SessionLocal, engine
from app.modules.fraud.models import FraudPattern
from app.modules.goals.models import GoalTemplate
from app.modules.learn.models import GlossaryTerm, Lesson, UserLearningStats
from app.modules.schemes.field_registry import validate_rule
from app.modules.schemes.models import Scheme, SchemeCategory, SchemeDocument, SchemeEligibilityRule, SchemeStep
from app.modules.users.models import NotificationSettings, User, UserProfile

SEED_DIR = Path(__file__).resolve().parent
EXPECTED_COUNTS = {"schemes": 28, "glossary_terms": 30, "lessons": 12}


def load(name: str):
    with open(SEED_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def word_count(text: str) -> int:
    return len(re.findall(r"[\w₹'’-]+", text))


# --- Validation -------------------------------------------------------------------

class SeedErrors(list):
    def need(self, cond: bool, msg: str) -> None:
        if not cond:
            self.append(msg)


def check_lengths(errors: SeedErrors, model, row: dict, label: str) -> None:
    """Every value must fit its String(n) column."""
    columns = Base.metadata.tables[model.__tablename__].columns
    for key, value in row.items():
        col = columns.get(key)
        if col is not None and isinstance(col.type, String) and col.type.length and isinstance(value, str):
            errors.need(len(value) <= col.type.length, f"{label}.{key}: {len(value)} chars > {col.type.length}")


def validate(data: dict) -> list[str]:
    e = SeedErrors()
    schemes, rules = data["schemes"]["schemes"], data["rules"]
    category_slugs = {c["slug"] for c in data["schemes"]["categories"]}
    scheme_slugs = [s["slug"] for s in schemes]

    e.need(len(scheme_slugs) == len(set(scheme_slugs)), "duplicate scheme slugs")
    e.need(set(scheme_slugs) == set(rules), f"schemes without rules or rules without scheme: {set(scheme_slugs) ^ set(rules)}")
    for s in schemes:
        label = f"scheme {s['slug']}"
        e.need(s["category_slug"] in category_slugs, f"{label}: unknown category {s['category_slug']}")
        e.need(4 <= len(s["steps"]) <= 6, f"{label}: needs 4–6 steps, has {len(s['steps'])}")
        e.need(bool(s["documents"]), f"{label}: no documents")
        e.need(s["official_url"].startswith("https://"), f"{label}: official_url must be https")
        check_lengths(e, Scheme, {k: v for k, v in s.items() if isinstance(v, str)}, label)
        for st in s["steps"]:
            check_lengths(e, SchemeStep, st, f"{label} step")
        for d in s["documents"]:
            check_lengths(e, SchemeDocument, {"document_name_en": d["name"]}, f"{label} document")
        keys = [r["rule_key"] for r in rules.get(s["slug"], [])]
        e.need(len(keys) == len(set(keys)), f"{label}: duplicate rule_key")
        for r in rules.get(s["slug"], []):
            err = validate_rule(r["field"], r["operator"], r["value"])
            e.need(err is None, f"{label} rule {r['rule_key']}: {err}")
            check_lengths(e, SchemeEligibilityRule, r, f"{label} rule {r['rule_key']}")
        if s["level"] == "state":
            e.need(any(r["field"] == "state_code" and r["value"] == s["state_code"] for r in rules[s["slug"]]),
                   f"{label}: state scheme needs a state_code rule")

    terms = data["glossary"]
    term_slugs = {t["slug"] for t in terms}
    e.need(len(term_slugs) == len(terms), "duplicate glossary slugs")
    for t in terms:
        label = f"term {t['slug']}"
        e.need(word_count(t["definition_en"]) <= 40, f"{label}: definition > 40 words ({word_count(t['definition_en'])})")
        e.need(word_count(t["key_takeaway_en"]) <= 15, f"{label}: key_takeaway > 15 words")
        e.need("₹" in t["example_en"], f"{label}: example needs ₹ figures")
        missing = set(t["related_slugs"]) - term_slugs
        e.need(not missing, f"{label}: unknown related slugs {missing}")
        e.need(t["slug"] not in t["related_slugs"], f"{label}: relates to itself")
        check_lengths(e, GlossaryTerm, t, label)

    lessons = data["lessons"]
    e.need(len({lesson["slug"] for lesson in lessons}) == len(lessons), "duplicate lesson slugs")
    for lesson in lessons:
        n = word_count(lesson["body_md_en"])
        e.need(150 <= n <= 300, f"lesson {lesson['slug']}: body is {n} words (needs 150–300)")
        check_lengths(e, Lesson, lesson, f"lesson {lesson['slug']}")

    for p in data["fraud"]:
        label = f"fraud {p['code']}"
        check_lengths(e, FraudPattern, p, label)
        if p["pattern_type"] == "regex":
            for pattern in p["patterns"]:
                try:
                    re.compile(pattern, re.IGNORECASE | re.UNICODE)
                except re.error as exc:
                    e.append(f"{label}: bad regex {pattern!r}: {exc}")
        e.need(p["pattern_type"] == "negative" or bool(p["reason_title_en"]), f"{label}: missing reason")

    for g in data["goal_templates"]:
        check_lengths(e, GoalTemplate, g, f"goal template {g['slug']}")

    for table, expected in EXPECTED_COUNTS.items():
        actual = {"schemes": len(schemes), "glossary_terms": len(terms), "lessons": len(lessons)}[table]
        e.need(actual == expected, f"expected {expected} {table}, found {actual}")
    return e


# --- Upserts ----------------------------------------------------------------------

async def upsert(session: AsyncSession, model, rows: list[dict], key: list[str], returning=None):
    if not rows:
        return []
    stmt = insert(model).values(rows)
    update_cols = {c: stmt.excluded[c] for c in rows[0] if c not in key}
    if "updated_at" in model.__table__.columns:
        update_cols["updated_at"] = func.now()
    stmt = stmt.on_conflict_do_update(index_elements=key, set_=update_cols)
    if returning is not None:
        stmt = stmt.returning(*returning)
        return (await session.execute(stmt)).all()
    await session.execute(stmt)
    return []


async def seed_schemes(session: AsyncSession, data: dict) -> None:
    verified = date.fromisoformat(data["schemes"]["last_verified_on"])
    await upsert(session, SchemeCategory, data["schemes"]["categories"], ["slug"])

    scheme_rows = [
        {
            "slug": s["slug"], "name_en": s["name_en"], "level": s["level"], "state_code": s["state_code"],
            "category_slug": s["category_slug"], "ministry_or_dept": s["ministry_or_dept"],
            "benefit_type": s["benefit_type"], "benefit_summary_en": s["benefit_summary_en"],
            "description_en": s["description_en"], "application_mode_en": s["application_mode_en"],
            "official_url": s["official_url"], "source_url": s["official_url"],
            "last_verified_on": verified, "deadline_on": s.get("deadline_on"), "is_active": True,
        }
        for s in data["schemes"]["schemes"]
    ]
    ids = dict(await upsert(session, Scheme, scheme_rows, ["slug"], returning=[Scheme.slug, Scheme.id]))

    for s in data["schemes"]["schemes"]:
        sid = ids[s["slug"]]
        rules = data["rules"][s["slug"]]
        await upsert(session, SchemeEligibilityRule, [{"scheme_id": sid, **r} for r in rules], ["scheme_id", "rule_key"])
        await session.execute(delete(SchemeEligibilityRule).where(
            SchemeEligibilityRule.scheme_id == sid,
            SchemeEligibilityRule.rule_key.not_in([r["rule_key"] for r in rules]),
        ))

        steps = [{"scheme_id": sid, "step_no": i, **st} for i, st in enumerate(s["steps"], start=1)]
        await upsert(session, SchemeStep, steps, ["scheme_id", "step_no"])
        await session.execute(delete(SchemeStep).where(SchemeStep.scheme_id == sid, SchemeStep.step_no > len(steps)))

        # Documents have no natural key: replace the scheme's list.
        await session.execute(delete(SchemeDocument).where(SchemeDocument.scheme_id == sid))
        session.add_all([
            SchemeDocument(scheme_id=sid, document_name_en=d["name"], is_mandatory=d["is_mandatory"], sort_order=i)
            for i, d in enumerate(s["documents"], start=1)
        ])
    await session.flush()


async def seed_admin(session: AsyncSession) -> str:
    phone = settings.ADMIN_PHONE_E164.strip()
    if not phone:
        return "skipped (ADMIN_PHONE_E164 is blank)"
    if not re.fullmatch(r"\+91[6-9]\d{9}", phone):
        raise SystemExit(f"ADMIN_PHONE_E164={phone!r} is not a valid +91 mobile number")
    stmt = insert(User).values(phone_e164=phone, role="admin", preferred_language="en")
    stmt = stmt.on_conflict_do_update(index_elements=["phone_e164"], set_={"role": "admin", "updated_at": func.now()})
    user_id = (await session.execute(stmt.returning(User.id))).scalar_one()
    for model in (UserProfile, NotificationSettings, UserLearningStats):
        await session.execute(insert(model).values(user_id=user_id).on_conflict_do_nothing())
    return f"ensured admin {phone[:3]} ••••• {phone[-5:]}"


async def counts(session: AsyncSession) -> dict[str, int]:
    tables = ["scheme_categories", "schemes", "scheme_eligibility_rules", "scheme_steps", "scheme_documents",
              "glossary_terms", "lessons", "fraud_patterns", "goal_templates", "users"]
    out = {}
    for t in tables:
        out[t] = (await session.execute(select(func.count()).select_from(Base.metadata.tables[t]))).scalar_one()
    return out


async def run(check_only: bool) -> None:
    data = {
        "schemes": load("schemes.json"),
        "rules": load("eligibility_rules.json"),
        "glossary": load("glossary.json"),
        "lessons": load("lessons.json"),
        "fraud": load("fraud_patterns.json"),
        "goal_templates": load("goal_templates.json"),
    }
    errors = validate(data)
    if errors:
        print(f"Seed validation failed ({len(errors)} problems):")
        for err in errors:
            print("  -", err)
        raise SystemExit(1)
    print("Seed data valid.")
    if check_only:
        return

    async with SessionLocal() as session, session.begin():
        await seed_schemes(session, data)
        await upsert(session, GlossaryTerm, [{**t, "is_active": True} for t in data["glossary"]], ["slug"])
        await upsert(session, Lesson, [{**lesson, "is_active": True} for lesson in data["lessons"]], ["slug"])
        await upsert(session, FraudPattern, [{**p, "is_active": True} for p in data["fraud"]], ["code"])
        await upsert(session, GoalTemplate, data["goal_templates"], ["slug"])
        admin_note = await seed_admin(session)
        result = await counts(session)

    print("Admin user:", admin_note)
    for table, n in result.items():
        print(f"  {table:26} {n}")
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Saathi shared content.")
    parser.add_argument("--check", action="store_true", help="validate the JSON files without writing")
    args = parser.parse_args()
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(run(args.check))


if __name__ == "__main__":
    main()
