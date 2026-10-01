/**
 * i18next setup (spec §3.1, §4.10). English is the source; hi/mr/ta must have identical keys and
 * identical {{placeholders}} — `npm run check:i18n` enforces it.
 */
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './en.json';
import hi from './hi.json';
import mr from './mr.json';
import ta from './ta.json';

export const LANGUAGES = ['en', 'hi', 'mr', 'ta'] as const;
export type Language = (typeof LANGUAGES)[number];

export function isLanguage(value: unknown): value is Language {
  return typeof value === 'string' && (LANGUAGES as readonly string[]).includes(value);
}

export const resources = {
  en: { translation: en },
  hi: { translation: hi },
  mr: { translation: mr },
  ta: { translation: ta },
} as const;

// Initialised once at import; the language store switches languages afterwards.
if (!i18n.isInitialized) {
  void i18n.use(initReactI18next).init({
    resources,
    lng: 'en',
    fallbackLng: 'en',
    interpolation: { escapeValue: false }, // React already escapes
    returnNull: false,
  });
}

export default i18n;
