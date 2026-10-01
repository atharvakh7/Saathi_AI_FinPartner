/** Connects the HTTP client to the stores. Called once from app/_layout.tsx. */
import { router } from 'expo-router';

import { api, configureClient } from './client';
import { queryClient } from './queryClient';
import { setLanguageServerSync, useLanguageStore } from '@/stores/language';
import { useSessionStore } from '@/stores/session';

let configured = false;

export function setupApi(): void {
  if (configured) return;
  configured = true;
  configureClient({
    getAccessToken: () => useSessionStore.getState().accessToken,
    getRefreshToken: () => useSessionStore.getState().refreshToken,
    getLanguage: () => useLanguageStore.getState().language,
    onTokensRefreshed: (tokens) => useSessionStore.getState().setTokens(tokens),
    onSessionExpired: async () => {
      await useSessionStore.getState().clearSession();
      queryClient.clear();
      router.replace('/onboarding/welcome');
    },
  });
  setLanguageServerSync(async (language) => {
    if (!useSessionStore.getState().refreshToken) return;
    const res = await api.patch('/me', { preferred_language: language });
    useSessionStore.getState().setUser(res.data);
  });
}
