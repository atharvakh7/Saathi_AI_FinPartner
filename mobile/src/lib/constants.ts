/** Enumerations shared with the backend (app/core/enums.py). Labels come from i18n. */

export const STATE_CODES = [
  'AN', 'AP', 'AR', 'AS', 'BR', 'CH', 'CG', 'DN', 'DL', 'GA', 'GJ', 'HR', 'HP', 'JK', 'JH', 'KA',
  'KL', 'LA', 'LD', 'MP', 'MH', 'MN', 'ML', 'MZ', 'NL', 'OD', 'PY', 'PB', 'RJ', 'SK', 'TN', 'TS',
  'TR', 'UP', 'UK', 'WB',
] as const;
export type StateCode = (typeof STATE_CODES)[number];

export const GENDERS = ['male', 'female', 'other', 'prefer_not_to_say'] as const;
export const AREA_TYPES = ['rural', 'urban'] as const;
export const OCCUPATIONS = ['farmer', 'student', 'gig_worker', 'senior_citizen', 'small_business_owner', 'salaried', 'other'] as const;
export const INCOME_PATTERNS = ['fixed_monthly', 'irregular', 'seasonal'] as const;
export const SOCIAL_CATEGORIES = ['general', 'obc', 'sc', 'st', 'prefer_not_to_say'] as const;

export const INCOME_CATEGORIES = [
  'crop_sale', 'wages', 'salary', 'gig_payout', 'allowance', 'pension', 'business', 'other_income',
] as const;
export const EXPENSE_CATEGORIES = [
  'food', 'housing_rent', 'utilities', 'transport', 'health', 'education', 'farm_inputs', 'debt_repayment',
  'insurance_premium', 'subscriptions', 'entertainment', 'other_expense',
] as const;
export type TxType = 'income' | 'expense';
export type TxCategory = (typeof INCOME_CATEGORIES)[number] | (typeof EXPENSE_CATEGORIES)[number];
export const CATEGORIES_BY_TYPE: Record<TxType, readonly TxCategory[]> = {
  income: INCOME_CATEGORIES, expense: EXPENSE_CATEGORIES,
};

export const DEBT_TYPES = [
  'bank_loan', 'kisan_credit_card', 'credit_card', 'microfinance', 'moneylender', 'family_friend', 'other',
] as const;
export type DebtType = (typeof DEBT_TYPES)[number];

/** Limits from the finance API (S15, S16). */
export const MAX_TX_AMOUNT = 10_000_000; // ₹1,00,00,000
export const MAX_DEBT_AMOUNT = 100_000_000;
export const MAX_INTEREST_PCT = 120;
export const NOTE_MAX = 200;

/** Phone entry (S04): 10-digit Indian mobile. */
export const MOBILE_RE = /^[6-9]\d{9}$/;

/** "By when?" choices for goals (S09), in months from today. */
export const GOAL_HORIZONS = [6, 12, 24, 36, 60] as const;

/** Version of the privacy notice the user agrees to (backend PRIVACY_NOTICE_VERSION). */
export const PRIVACY_VERSION = '1.1';
