/** Build-time configuration from mobile/.env (EXPO_PUBLIC_* are inlined by Expo). */
import type { Language } from '@/i18n';

const LANGUAGES = ['en', 'hi', 'mr', 'ta'] as const;

function language(value: string | undefined): Language {
  return (LANGUAGES as readonly string[]).includes(value ?? '') ? (value as Language) : 'en';
}

export const config = {
  apiBaseUrl: (process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://10.0.2.2:8000/api/v1').replace(/\/+$/, ''),
  defaultLanguage: language(process.env.EXPO_PUBLIC_DEFAULT_LANGUAGE),
  grievanceEmail: process.env.EXPO_PUBLIC_GRIEVANCE_EMAIL ?? 'grievance@example.com',
  easProjectId: process.env.EXPO_PUBLIC_EAS_PROJECT_ID ?? '',
  /** Network timeout; chat and voice replies can take ~30 s on the local LLM. */
  requestTimeoutMs: 60_000,
} as const;
