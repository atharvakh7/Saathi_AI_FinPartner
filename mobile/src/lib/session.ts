/** Login/logout helpers and the `['me']` query shared by S01 and onboarding. */
import { useQuery } from '@tanstack/react-query';

import { getMe, logout as apiLogout, patchMe } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import type { MeDTO, OtpVerifyDTO } from '@/api/types';
import { useLanguageStore } from '@/stores/language';
import { isLoggedIn, useSessionStore } from '@/stores/session';
import { routeForSession } from './routing';

export const ME_KEY = ['me'] as const;

export function useMe(enabled = true) {
  const loggedIn = useSessionStore(isLoggedIn);
  return useQuery({ queryKey: ME_KEY, queryFn: getMe, enabled: enabled && loggedIn });
}

/**
 * After OTP verify: store tokens, save the language chosen on Welcome to the account (the explicit
 * choice wins over the account default), and return where to go next.
 */
export async function completeLogin(res: OtpVerifyDTO): Promise<string> {
  await useSessionStore.getState().setSession(res, res.user);
  const language = useLanguageStore.getState().language;
  if (res.user.preferred_language !== language) {
    try {
      useSessionStore.getState().setUser(await patchMe({ preferred_language: language }));
    } catch {
      // not fatal: the UI keeps the chosen language; it is saved again next time it changes
    }
  }
  return routeForSession(true, await refreshMe());
}

/** Fetch a fresh /me into the cache (also when no screen is currently observing it). */
export async function refreshMe(): Promise<MeDTO> {
  return queryClient.fetchQuery<MeDTO>({ queryKey: ME_KEY, queryFn: getMe, staleTime: 0 });
}

/** Re-read /me after an onboarding step and go to the next unfinished one. */
export async function nextOnboardingRoute(): Promise<string> {
  const me = await refreshMe();
  return routeForSession(true, me);
}

export async function signOut(): Promise<void> {
  const refresh = useSessionStore.getState().refreshToken;
  if (refresh) {
    try {
      await apiLogout(refresh);
    } catch {
      // already invalid or offline: the local session is cleared anyway
    }
  }
  await useSessionStore.getState().clearSession();
  queryClient.clear();
}
