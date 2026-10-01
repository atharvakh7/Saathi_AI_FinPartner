/** useSessionStore (spec §4.3): tokens in SecureStore, user in memory. */
import { create } from 'zustand';

import type { TokenPair, UserDTO } from '@/api/types';
import { deleteItem, getItem, KEYS, setItem } from '@/lib/storage';

interface SessionState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserDTO | null;
  isHydrated: boolean;
  setSession: (tokens: TokenPair, user?: UserDTO | null) => Promise<void>;
  setTokens: (tokens: TokenPair) => Promise<void>;
  setUser: (user: UserDTO | null) => void;
  clearSession: () => Promise<void>;
  hydrateFromSecureStore: () => Promise<void>;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  isHydrated: false,

  async setSession(tokens, user) {
    await get().setTokens(tokens);
    if (user !== undefined) set({ user });
  },

  async setTokens({ access_token, refresh_token }) {
    set({ accessToken: access_token, refreshToken: refresh_token });
    await Promise.all([setItem(KEYS.accessToken, access_token), setItem(KEYS.refreshToken, refresh_token)]);
  },

  setUser(user) {
    set({ user });
  },

  async clearSession() {
    set({ accessToken: null, refreshToken: null, user: null });
    await Promise.all([deleteItem(KEYS.accessToken), deleteItem(KEYS.refreshToken)]);
  },

  async hydrateFromSecureStore() {
    const [accessToken, refreshToken] = await Promise.all([getItem(KEYS.accessToken), getItem(KEYS.refreshToken)]);
    set({ accessToken, refreshToken, isHydrated: true });
  },
}));

export const isLoggedIn = (s: Pick<SessionState, 'accessToken' | 'refreshToken'>) => Boolean(s.refreshToken);
