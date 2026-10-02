/** Build-time configuration from mobile/.env (EXPO_PUBLIC_* are inlined by Expo). */
import { Platform } from 'react-native';
import Constants from 'expo-constants';

import type { Language } from '@/i18n';

const LANGUAGES = ['en', 'hi', 'mr', 'ta'] as const;

function language(value: string | undefined): Language {
  return (LANGUAGES as readonly string[]).includes(value ?? '') ? (value as Language) : 'en';
}

/**
 * API base URL. `localhost` only works in the browser on the dev PC; on a phone in Expo Go it would
 * point at the phone itself. So on native, a localhost URL is rewritten to the PC address that Expo Go
 * loaded the app from (Constants.expoConfig.hostUri, e.g. "192.168.1.20:8081").
 */
export function resolveApiBase(raw: string, platform: string, hostUri: string | null | undefined): string {
  const url = raw.replace(/\/+$/, '');
  if (platform === 'web') return url;
  const host = hostUri?.split(':')[0];
  if (!host || host === 'localhost' || host === '127.0.0.1') return url;
  return url.replace(/\/\/(localhost|127\.0\.0\.1)(?=[:/]|$)/, `//${host}`);
}

export const config = {
  apiBaseUrl: resolveApiBase(process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://10.0.2.2:8000/api/v1', Platform.OS, Constants.expoConfig?.hostUri),
  defaultLanguage: language(process.env.EXPO_PUBLIC_DEFAULT_LANGUAGE),
  grievanceEmail: process.env.EXPO_PUBLIC_GRIEVANCE_EMAIL ?? 'grievance@example.com',
  easProjectId: process.env.EXPO_PUBLIC_EAS_PROJECT_ID ?? '',
  /** Network timeout; chat and voice replies can take ~30 s on the local LLM. */
  requestTimeoutMs: 60_000,
} as const;
