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

/** Phone entry (S04): 10-digit Indian mobile. */
export const MOBILE_RE = /^[6-9]\d{9}$/;

/** "By when?" choices for goals (S09), in months from today. */
export const GOAL_HORIZONS = [6, 12, 24, 36, 60] as const;

/** Version of the privacy notice the user agrees to (backend PRIVACY_NOTICE_VERSION). */
export const PRIVACY_VERSION = '1.0';
