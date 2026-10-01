/** Typed API calls (spec §7). One function per endpoint; screens use these with React Query. */
import { Platform } from 'react-native';

import type { Language } from '@/i18n';
import { api } from './client';
import type { ISODate, MeDTO, OtpVerifyDTO, ProfileDTO, UserDTO } from './types';

// --- Auth ---------------------------------------------------------------------------

export interface OtpRequestDTO {
  request_id: string;
  expires_in_sec: number;
  resend_after_sec: number;
}

export async function requestOtp(phoneE164: string): Promise<OtpRequestDTO> {
  return (await api.post<OtpRequestDTO>('/auth/otp/request', { phone_e164: phoneE164 })).data;
}

export async function verifyOtp(phoneE164: string, code: string): Promise<OtpVerifyDTO> {
  const platform = Platform.OS === 'android' || Platform.OS === 'ios' ? Platform.OS : undefined;
  return (await api.post<OtpVerifyDTO>('/auth/otp/verify', { phone_e164: phoneE164, code, platform })).data;
}

export async function logout(refreshToken: string): Promise<void> {
  await api.post('/auth/logout', { refresh_token: refreshToken });
}

// --- Me ------------------------------------------------------------------------------

export async function getMe(): Promise<MeDTO> {
  return (await api.get<MeDTO>('/me')).data;
}

export async function patchMe(body: { preferred_language?: Language; voice_reply_enabled?: boolean }): Promise<UserDTO> {
  return (await api.patch<UserDTO>('/me', body)).data;
}

export type ConsentType = 'terms_privacy' | 'personalization' | 'push_notifications';

export async function postConsents(consents: { consent_type: ConsentType; granted: boolean }[], version: string) {
  return (await api.post('/me/consents', { consents, version })).data;
}

export type ProfileInput = Partial<Omit<ProfileDTO, 'confidence_score_pct' | 'confidence_level' | 'onboarding_completed_at'>>;

export async function putProfile(body: ProfileInput): Promise<ProfileDTO> {
  return (await api.put<ProfileDTO>('/me/profile', body)).data;
}

export async function postConfidence(answers: number[]): Promise<{ score_pct: number | null; level: string | null }> {
  return (await api.post('/me/confidence-assessment', { answers })).data;
}

export async function completeOnboarding(): Promise<UserDTO> {
  return (await api.post<UserDTO>('/me/onboarding-complete')).data;
}

export interface PrivacyNoticeDTO {
  version: string;
  language: Language;
  markdown: string;
}

export async function getPrivacyNotice(lang: Language): Promise<PrivacyNoticeDTO> {
  return (await api.get<PrivacyNoticeDTO>('/legal/privacy-notice', { params: { lang } })).data;
}

// --- Goals & plan --------------------------------------------------------------------

export interface GoalTemplateDTO {
  slug: string;
  title: string;
  category: string;
  default_target_inr: number | null;
}

export async function getGoalTemplates(): Promise<GoalTemplateDTO[]> {
  return (await api.get<GoalTemplateDTO[]>('/goals/templates')).data;
}

export interface GoalInput {
  title: string;
  category: string;
  target_amount_inr: number;
  target_date?: ISODate | null;
}

export async function createGoal(body: GoalInput) {
  return (await api.post('/goals', body)).data;
}

export interface EmergencyFundDTO {
  exists: boolean;
  target_months: number;
  monthly_essential_expense_inr: number;
  target_amount_inr: number;
  current_amount_inr: number;
  pct: number;
  suggested_monthly_contribution_inr: number;
  estimated_completion_date: ISODate | null;
  goal_id: string | null;
}

export async function getEmergencyFund(): Promise<EmergencyFundDTO> {
  return (await api.get<EmergencyFundDTO>('/plan/emergency-fund')).data;
}

// --- Settings (S35–S40) --------------------------------------------------------------

export interface ConsentDTO {
  consent_type: ConsentType;
  granted: boolean;
  version: string;
  updated_at: string;
}

export async function getConsents(): Promise<ConsentDTO[]> {
  return (await api.get<ConsentDTO[]>('/me/consents')).data;
}

export interface NotificationSettingsDTO {
  push_enabled: boolean;
  daily_insight_enabled: boolean;
  daily_insight_time: string; // "HH:MM" or "HH:MM:SS"
  income_reminder_enabled: boolean;
  goal_reminder_enabled: boolean;
  scheme_deadline_enabled: boolean;
  lean_month_alert_enabled: boolean;
  streak_reminder_enabled: boolean;
  streak_reminder_time: string;
}

export async function getNotificationSettings(): Promise<NotificationSettingsDTO> {
  return (await api.get<NotificationSettingsDTO>('/me/notification-settings')).data;
}

export async function putNotificationSettings(body: Partial<NotificationSettingsDTO>): Promise<NotificationSettingsDTO> {
  return (await api.put<NotificationSettingsDTO>('/me/notification-settings', body)).data;
}

/** GET /me/export as text (the JSON file the user downloads). */
export async function exportMyData(): Promise<string> {
  const res = await api.get('/me/export', { responseType: 'text', transformResponse: (d: unknown) => d });
  return typeof res.data === 'string' ? res.data : JSON.stringify(res.data, null, 2);
}

export async function deleteAccount(): Promise<void> {
  await api.delete('/me', { data: { confirm: 'DELETE' } });
}

export interface MemoryFactDTO {
  id: string;
  category: 'preference' | 'fact' | 'goal_context' | 'concern' | 'behavior';
  fact_text: string;
  importance: number;
  created_at: string;
}

export async function listMemory(): Promise<MemoryFactDTO[]> {
  return (await api.get<MemoryFactDTO[]>('/memory')).data;
}

export async function deleteMemoryFact(id: string): Promise<void> {
  await api.delete(`/memory/${id}`);
}

export async function forgetEverything(): Promise<void> {
  await api.delete('/memory');
}
