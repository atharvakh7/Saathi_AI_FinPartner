/**
 * API DTOs shared across screens (spec §7.3), matching the FastAPI response models.
 * Feature-specific DTOs are added next to their screens in later steps.
 */
import type { Language } from '@/i18n';

export type ISODate = string; // "2026-09-30"
export type ISODateTime = string; // "2026-09-30T10:00:00Z"

export type OnboardingStep = 'consent' | 'profile' | 'confidence' | 'goals';

export interface UserDTO {
  id: string;
  phone_masked: string;
  role: 'user' | 'admin';
  preferred_language: Language;
  voice_reply_enabled: boolean;
  onboarding_completed_at: ISODateTime | null;
  first_name: string | null;
}

export interface ProfileDTO {
  full_name: string | null;
  age_years: number | null;
  gender: string | null;
  state_code: string | null;
  district: string | null;
  area_type: string | null;
  occupation_type: string | null;
  income_pattern: string | null;
  declared_monthly_income_min_inr: number | null;
  declared_monthly_income_max_inr: number | null;
  household_size: number | null;
  dependents_count: number | null;
  annual_household_income_inr: number | null;
  land_holding_hectares: number | string | null;
  social_category: string | null;
  has_bank_account: boolean | null;
  is_land_owner: boolean | null;
  is_bpl_household: boolean | null;
  is_income_tax_payer: boolean | null;
  is_student: boolean | null;
  is_street_vendor: boolean | null;
  is_unorganised_worker: boolean | null;
  is_traditional_artisan: boolean | null;
  has_pucca_house: boolean | null;
  has_girl_child_below_10: boolean | null;
  is_head_of_household: boolean | null;
  is_govt_employee: boolean | null;
  confidence_score_pct: number | null;
  confidence_level: string | null;
  voice_reply_enabled: boolean;
  onboarding_completed_at: ISODateTime | null;
}

export interface MeDTO {
  user: UserDTO;
  profile: ProfileDTO | null;
  needs: OnboardingStep | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface OtpVerifyDTO extends TokenPair {
  is_new_user: boolean;
  user: UserDTO;
}

export interface Page<T> {
  items: T[];
  next_cursor: string | null;
}

/** Error envelope (spec §7.1): {"error": {code, message, details, request_id}}. */
export interface ErrorEnvelope {
  error: { code: string; message: string; details: unknown; request_id?: string };
}

export interface TransactionDraft {
  type: 'income' | 'expense';
  amount_inr: number;
  category: string;
  occurred_on: ISODate;
  note: string | null;
}
