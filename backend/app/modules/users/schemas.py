"""User/profile DTOs (spec §7.3 UserDTO, §7.4 /me)."""

import uuid
from datetime import datetime, time
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_serializer, field_validator

from app.core import enums

Language = Literal["en", "hi", "mr", "ta"]
OnboardingStep = Literal["consent", "profile", "confidence", "goals"]
ConsentType = Literal["terms_privacy", "personalization", "push_notifications"]

Gender = Literal[enums.GENDERS]  # type: ignore[valid-type]
StateCode = Literal[enums.STATE_CODES]  # type: ignore[valid-type]
AreaType = Literal[enums.AREA_TYPES]  # type: ignore[valid-type]
Occupation = Literal[enums.OCCUPATION_TYPES]  # type: ignore[valid-type]
IncomePattern = Literal[enums.INCOME_PATTERNS]  # type: ignore[valid-type]
SocialCategory = Literal[enums.SOCIAL_CATEGORIES]  # type: ignore[valid-type]


class UserOut(BaseModel):
    """UserDTO."""

    id: uuid.UUID
    phone_masked: str
    role: Literal["user", "admin"]
    preferred_language: Language
    voice_reply_enabled: bool
    onboarding_completed_at: datetime | None
    first_name: str | None


class ProfileOut(BaseModel):
    """ProfileDTO: all user_profiles columns except internal ones."""

    model_config = ConfigDict(from_attributes=True)

    full_name: str | None
    age_years: int | None
    gender: str | None
    state_code: str | None
    district: str | None
    area_type: str | None
    occupation_type: str | None
    income_pattern: str | None
    declared_monthly_income_min_inr: int | None
    declared_monthly_income_max_inr: int | None
    household_size: int | None
    dependents_count: int | None
    annual_household_income_inr: int | None
    land_holding_hectares: Decimal | None
    social_category: str | None
    has_bank_account: bool | None
    is_land_owner: bool | None
    is_bpl_household: bool | None
    is_income_tax_payer: bool | None
    is_student: bool | None
    is_street_vendor: bool | None
    is_unorganised_worker: bool | None
    is_traditional_artisan: bool | None
    has_pucca_house: bool | None
    has_girl_child_below_10: bool | None
    is_head_of_household: bool | None
    is_govt_employee: bool | None
    confidence_score_pct: int | None
    confidence_level: str | None
    voice_reply_enabled: bool
    onboarding_completed_at: datetime | None


class MeOut(BaseModel):
    user: UserOut
    profile: ProfileOut | None
    needs: OnboardingStep | None


class MePatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preferred_language: Language | None = None
    voice_reply_enabled: bool | None = None


# --- Profile -----------------------------------------------------------------------

class ProfileIn(BaseModel):
    """PUT /me/profile: any subset of profile fields (spec §4.7 S07/S36 validation).

    Only fields present in the body are changed; an explicit null clears a field
    (except the onboarding-required ones, see users.service.REQUIRED_PROFILE_FIELDS).
    """

    model_config = ConfigDict(extra="forbid")

    full_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)] | None = None
    age_years: int | None = Field(default=None, ge=18, le=100)
    gender: Gender | None = None
    state_code: StateCode | None = None
    district: Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)] | None = None
    area_type: AreaType | None = None
    occupation_type: Occupation | None = None
    income_pattern: IncomePattern | None = None
    declared_monthly_income_min_inr: int | None = Field(default=None, ge=0, le=100_000_000)
    declared_monthly_income_max_inr: int | None = Field(default=None, ge=0, le=100_000_000)
    household_size: int | None = Field(default=None, ge=1, le=20)
    dependents_count: int | None = Field(default=None, ge=0, le=19)
    annual_household_income_inr: int | None = Field(default=None, ge=0, le=1_000_000_000)
    land_holding_hectares: Decimal | None = Field(default=None, ge=0, le=500, max_digits=6, decimal_places=2)
    social_category: SocialCategory | None = None
    has_bank_account: bool | None = None
    is_land_owner: bool | None = None
    is_bpl_household: bool | None = None
    is_income_tax_payer: bool | None = None
    is_student: bool | None = None
    is_street_vendor: bool | None = None
    is_unorganised_worker: bool | None = None
    is_traditional_artisan: bool | None = None
    has_pucca_house: bool | None = None
    has_girl_child_below_10: bool | None = None
    is_head_of_household: bool | None = None
    is_govt_employee: bool | None = None
    voice_reply_enabled: bool | None = None


# --- Confidence assessment ---------------------------------------------------------

class ConfidenceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answers: list[Annotated[int, Field(ge=1, le=5)]]

    @field_validator("answers")
    @classmethod
    def _five_or_skip(cls, v: list[int]) -> list[int]:
        if len(v) not in (0, 5):
            raise ValueError("send exactly 5 answers, or [] to skip")
        return v


class ConfidenceOut(BaseModel):
    score_pct: int | None
    level: Literal["low", "medium", "high"] | None


# --- Consents ----------------------------------------------------------------------

class ConsentItemIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consent_type: ConsentType
    granted: bool


class ConsentsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consents: list[ConsentItemIn] = Field(min_length=1, max_length=3)
    version: str = Field(min_length=1, max_length=10)

    @field_validator("consents")
    @classmethod
    def _unique_types(cls, v: list[ConsentItemIn]) -> list[ConsentItemIn]:
        if len({c.consent_type for c in v}) != len(v):
            raise ValueError("each consent_type may appear once")
        return v


class ConsentOut(BaseModel):
    consent_type: ConsentType
    granted: bool
    version: str
    updated_at: datetime


# --- Device tokens -----------------------------------------------------------------

class DeviceTokenIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expo_push_token: str = Field(pattern=r"^Expo(nent)?PushToken\[[^\]]{1,180}\]$", max_length=200)
    platform: Literal["android", "ios"]


class DeviceTokenOut(BaseModel):
    id: uuid.UUID


# --- Notification settings ---------------------------------------------------------

class NotificationSettingsBase(BaseModel):
    @field_serializer("daily_insight_time", "streak_reminder_time", check_fields=False)
    def _hhmm(self, v: time | None) -> str | None:
        return v.strftime("%H:%M") if v else None


class NotificationSettingsOut(NotificationSettingsBase):
    model_config = ConfigDict(from_attributes=True)

    push_enabled: bool
    daily_insight_enabled: bool
    daily_insight_time: time
    income_reminder_enabled: bool
    goal_reminder_enabled: bool
    scheme_deadline_enabled: bool
    lean_month_alert_enabled: bool
    streak_reminder_enabled: bool
    streak_reminder_time: time


class NotificationSettingsIn(BaseModel):
    """PUT body: any subset; times as "HH:MM"."""

    model_config = ConfigDict(extra="forbid")

    push_enabled: bool | None = None
    daily_insight_enabled: bool | None = None
    daily_insight_time: time | None = None
    income_reminder_enabled: bool | None = None
    goal_reminder_enabled: bool | None = None
    scheme_deadline_enabled: bool | None = None
    lean_month_alert_enabled: bool | None = None
    streak_reminder_enabled: bool | None = None
    streak_reminder_time: time | None = None

    @field_validator("daily_insight_time", "streak_reminder_time", mode="before")
    @classmethod
    def _parse_hhmm(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%H:%M").time()
            except ValueError as exc:
                raise ValueError("use HH:MM (24-hour)") from exc
        return v


# --- Account -----------------------------------------------------------------------

class DeleteMeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm: str


class PrivacyNoticeOut(BaseModel):
    version: str
    language: Language
    markdown: str
