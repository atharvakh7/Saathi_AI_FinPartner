"""Rule evaluator (spec §5.6). Pure functions: no database, no I/O.

Each rule -> "pass" | "fail" | "unknown" (profile value missing). Scheme status:
  not_eligible       any mandatory rule fails
  eligible           every mandatory rule passes
  possibly_eligible  otherwise (some mandatory rule unknown, none failed)
Non-mandatory rules only add explanation text.

"prefer_not_to_say" (gender, social_category) is treated as unknown: the user chose not to tell us,
so a rule on it can neither pass nor fail. It is not asked again (the profile value is not null).
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from app.modules.schemes.field_registry import FIELDS

PASS, FAIL, UNKNOWN = "pass", "fail", "unknown"
UNDISCLOSED = "prefer_not_to_say"


@dataclass(frozen=True)
class RuleIn:
    rule_key: str
    field: str
    operator: str
    value: Any
    is_mandatory: bool
    explanation_en: str


def profile_values(profile) -> dict[str, Any]:
    """Registry field -> profile value (None when unknown). `profile` may be None."""
    values = {name: getattr(profile, name, None) if profile is not None else None for name in FIELDS}
    for name, value in values.items():
        if value == UNDISCLOSED:
            values[name] = None
    return values


def evaluate_rule(operator: str, expected: Any, actual: Any) -> str:
    if actual is None:
        return UNKNOWN
    if operator == "is_true":
        ok = actual is True
    elif operator == "is_false":
        ok = actual is False
    elif operator == "eq":
        ok = actual == expected
    elif operator == "neq":
        ok = actual != expected
    elif operator == "in":
        ok = actual in expected
    elif operator == "not_in":
        ok = actual not in expected
    elif operator == "gte":
        ok = actual >= expected
    elif operator == "lte":
        ok = actual <= expected
    elif operator == "between":
        ok = expected[0] <= actual <= expected[1]
    else:
        raise ValueError(f"unknown operator {operator!r}")
    return PASS if ok else FAIL


def evaluate_scheme(rules: Iterable[RuleIn], values: dict[str, Any]) -> tuple[str, list[dict]]:
    """Returns (status, rule_results) with rule_results = [{rule_key, field, result, explanation, mandatory}]."""
    results = []
    for rule in rules:
        results.append({
            "rule_key": rule.rule_key,
            "field": rule.field,
            "result": evaluate_rule(rule.operator, rule.value, values.get(rule.field)),
            "explanation": rule.explanation_en,
            "mandatory": rule.is_mandatory,
        })
    mandatory = [r["result"] for r in results if r["mandatory"]]
    if FAIL in mandatory:
        status = "not_eligible"
    elif UNKNOWN in mandatory:
        status = "possibly_eligible"
    else:
        status = "eligible"
    return status, results


def missing_fields(rule_results: list[dict]) -> list[str]:
    """Fields whose answer could still decide a possibly-eligible scheme (mandatory and unknown)."""
    seen = []
    for r in rule_results:
        if r.get("mandatory", True) and r["result"] == UNKNOWN and r["field"] not in seen:
            seen.append(r["field"])
    return seen


def failed_rules(rule_results: list[dict]) -> list[dict]:
    return [r for r in rule_results if r.get("mandatory", True) and r["result"] == FAIL]
