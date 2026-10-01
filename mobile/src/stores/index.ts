/** Small UI stores (spec §4.3). Session and language live in their own files. */
import { create } from 'zustand';

import type { TransactionDraft } from '@/api/types';

export { isLoggedIn, useSessionStore } from './session';
export { deviceLanguage, useLanguageStore } from './language';

interface ChatState {
  activeConversationId: string | null;
  isRecording: boolean;
  isPlaying: boolean;
  pendingTransactionDraft: TransactionDraft | null;
  setActiveConversation: (id: string | null) => void;
  setRecording: (v: boolean) => void;
  setPlaying: (v: boolean) => void;
  setPendingDraft: (d: TransactionDraft | null) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  activeConversationId: null,
  isRecording: false,
  isPlaying: false,
  pendingTransactionDraft: null,
  setActiveConversation: (id) => set({ activeConversationId: id }),
  setRecording: (v) => set({ isRecording: v }),
  setPlaying: (v) => set({ isPlaying: v }),
  setPendingDraft: (d) => set({ pendingTransactionDraft: d }),
}));

/** In-progress onboarding answers, kept until submitted (S07–S09). */
export type OnboardingValues = Record<string, string | number | boolean | null | string[]>;

interface OnboardingState {
  values: OnboardingValues;
  update: (patch: OnboardingValues) => void;
  reset: () => void;
}

export const useOnboardingStore = create<OnboardingState>((set) => ({
  values: {},
  update: (patch) => set((s) => ({ values: { ...s.values, ...patch } })),
  reset: () => set({ values: {} }),
}));

export type ToastType = 'info' | 'success' | 'error';

interface UiState {
  termSheetSlug: string | null;
  toast: { message: string; type: ToastType } | null;
  openTerm: (slug: string | null) => void;
  showToast: (message: string, type?: ToastType) => void;
  hideToast: () => void;
}

export const useUiStore = create<UiState>((set) => ({
  termSheetSlug: null,
  toast: null,
  openTerm: (slug) => set({ termSheetSlug: slug }),
  showToast: (message, type = 'info') => set({ toast: { message, type } }),
  hideToast: () => set({ toast: null }),
}));
