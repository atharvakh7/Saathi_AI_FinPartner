"""Profile fields usable in scheme eligibility rules (spec §5.6).

`type` drives rule validation, the eligibility questions endpoint and answer parsing.
`lazy=True` fields are not asked during onboarding; they are collected by /schemes/check.
"""

from dataclasses import dataclass

from app.core import enums


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type: str  # "int" | "enum" | "str" | "bool"
    options: tuple[str, ...] | None = None
    lazy: bool = False


FIELDS: dict[str, FieldSpec] = {
    f.name: f
    for f in (
        FieldSpec("age_years", "int"),
        FieldSpec("gender", "enum", enums.GENDERS),
        FieldSpec("state_code", "str", enums.STATE_CODES),
        FieldSpec("area_type", "enum", enums.AREA_TYPES),
        FieldSpec("occupation_type", "enum", enums.OCCUPATION_TYPES),
        FieldSpec("is_land_owner", "bool"),
        FieldSpec("annual_household_income_inr", "int", lazy=True),
        FieldSpec("declared_monthly_income_max_inr", "int"),
        FieldSpec("social_category", "enum", enums.SOCIAL_CATEGORIES),
        FieldSpec("is_bpl_household", "bool", lazy=True),
        FieldSpec("is_income_tax_payer", "bool", lazy=True),
        FieldSpec("has_bank_account", "bool"),
        FieldSpec("is_student", "bool", lazy=True),
        FieldSpec("is_street_vendor", "bool", lazy=True),
        FieldSpec("is_unorganised_worker", "bool", lazy=True),
        FieldSpec("is_traditional_artisan", "bool", lazy=True),
        FieldSpec("has_pucca_house", "bool", lazy=True),
        FieldSpec("has_girl_child_below_10", "bool", lazy=True),
        FieldSpec("is_head_of_household", "bool", lazy=True),
        FieldSpec("is_govt_employee", "bool", lazy=True),
    )
}

# Operators valid for each field type.
OPERATORS_BY_TYPE: dict[str, set[str]] = {
    "int": {"eq", "neq", "in", "not_in", "gte", "lte", "between"},
    "enum": {"eq", "neq", "in", "not_in"},
    "str": {"eq", "neq", "in", "not_in"},
    "bool": {"is_true", "is_false"},
}


def validate_rule(field: str, operator: str, value) -> str | None:
    """Returns an error message, or None when the rule is valid."""
    spec = FIELDS.get(field)
    if spec is None:
        return f"unknown field '{field}'"
    if operator not in OPERATORS_BY_TYPE[spec.type]:
        return f"operator '{operator}' not allowed for {spec.type} field '{field}'"
    if operator in ("is_true", "is_false"):
        return None if value is None else "is_true/is_false take no value"
    if operator == "between":
        ok = isinstance(value, list) and len(value) == 2 and all(isinstance(v, (int, float)) for v in value)
        return None if ok and value[0] <= value[1] else "between needs [lo, hi]"
    if operator in ("in", "not_in"):
        if not isinstance(value, list) or not value:
            return f"{operator} needs a non-empty list"
        values = value
    else:
        values = [value]
    for v in values:
        if spec.type == "int" and not isinstance(v, (int, float)):
            return f"value {v!r} must be a number"
        if spec.options and v not in spec.options:
            return f"value {v!r} not one of {spec.options}"
    return None
