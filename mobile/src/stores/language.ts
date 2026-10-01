/**
 * useLanguageStore (spec §4.3): UI language persisted under SecureStore key `lang`.
 * setLanguage also switches i18next and, when logged in, saves it with PATCH /me.
 */
import { getLocales } from 'expo-localization';
import { create } from 'zustand';

import { config } from '@/config';
import i18n, { isLanguage, type Language } from '@/i18n';
import { getItem, KEYS, setItem } from '@/lib/storage';

interface LanguageState {
  language: Language;
  setLanguage: (language: Language, options?: { syncServer?: boolean }) => Promise<void>;
  hydrate: () => Promise<void>;
}

/** Device language if we support it, else the build default. */
export function deviceLanguage(): Language {
  const code = getLocales()[0]?.languageCode ?? undefined;
  return isLanguage(code) ? code : config.defaultLanguage;
}

// Set by the app at start-up (avoids a store -> api -> store import cycle).
let saveToServer: ((language: Language) => Promise<void>) | null = null;
export function setLanguageServerSync(fn: (language: Language) => Promise<void>) {
  saveToServer = fn;
}

export const useLanguageStore = create<LanguageState>((set) => ({
  language: 'en',

  async setLanguage(language, options = {}) {
    set({ language });
    await i18n.changeLanguage(language);
    await setItem(KEYS.language, language);
    if (options.syncServer !== false && saveToServer) {
      try {
        await saveToServer(language);
      } catch {
        // offline or logged out: the local choice still applies; it's sent again on next login
      }
    }
  },

  async hydrate() {
    const saved = await getItem(KEYS.language);
    const language = isLanguage(saved) ? saved : deviceLanguage();
    set({ language });
    await i18n.changeLanguage(language);
  },
}));
