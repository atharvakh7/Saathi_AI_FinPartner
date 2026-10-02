/** Typed API calls (spec §7). One function per endpoint; screens use these with React Query. */
import { Platform } from 'react-native';

import type { Language } from '@/i18n';
import type { ChatCardData } from '@/components/chat';
import type { DebtType, TxCategory, TxType } from '@/lib/constants';
import type { TermSpan } from '@/lib/highlight';
import { api } from './client';
import type { ISODate, MeDTO, OtpVerifyDTO, Page, ProfileDTO, TransactionDraft, UserDTO } from './types';

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

// --- Finance (S10, S14–S16) ----------------------------------------------------------

export interface SummaryDTO {
  month: string; // "YYYY-MM"
  income_inr: number;
  expenses_inr: number;
  savings_inr: number;
  debt_outstanding_inr: number;
  active_debts_count: number;
  active_goals_count: number;
  emergency_fund: { exists: boolean; pct: number; expected_pct: number; on_track: boolean | null };
  risk: { score: number; level: 'low' | 'medium' | 'high'; computed_on: ISODate } | null;
  unread_notifications: number;
  has_transactions: boolean;
}

export async function getSummary(month?: string): Promise<SummaryDTO> {
  return (await api.get<SummaryDTO>('/finance/summary', { params: month ? { month } : {} })).data;
}

export interface TransactionDTO {
  id: string;
  type: TxType;
  amount_inr: number;
  category: TxCategory;
  is_essential: boolean;
  occurred_on: ISODate;
  note: string | null;
  source: 'manual' | 'voice' | 'chat';
  created_at: string;
}

export interface TransactionInput {
  type: TxType;
  amount_inr: number;
  category: TxCategory;
  occurred_on: ISODate;
  note: string | null;
}

export async function listTransactions(params: {
  month?: string; type?: TxType; cursor?: string | null; limit?: number;
}): Promise<Page<TransactionDTO>> {
  const query: Record<string, string | number> = {};
  if (params.month) query.month = params.month;
  if (params.type) query.type = params.type;
  if (params.cursor) query.cursor = params.cursor;
  if (params.limit) query.limit = params.limit;
  return (await api.get<Page<TransactionDTO>>('/transactions', { params: query })).data;
}

export async function createTransaction(body: TransactionInput): Promise<TransactionDTO> {
  return (await api.post<TransactionDTO>('/transactions', { ...body, source: 'manual' })).data;
}

export async function updateTransaction(id: string, body: Partial<TransactionInput>): Promise<TransactionDTO> {
  return (await api.patch<TransactionDTO>(`/transactions/${id}`, body)).data;
}

export async function deleteTransaction(id: string): Promise<void> {
  await api.delete(`/transactions/${id}`);
}

export async function parseTransaction(text: string, language: Language): Promise<{ draft: TransactionDraft; confidence: number }> {
  return (await api.post('/transactions/parse', { text, language })).data;
}

export interface DebtDTO {
  id: string;
  lender_name: string;
  debt_type: DebtType;
  principal_outstanding_inr: number;
  interest_rate_pct: number;
  min_monthly_payment_inr: number;
  due_day_of_month: number | null;
  status: 'active' | 'closed';
}

export interface DebtInput {
  lender_name: string;
  debt_type: DebtType;
  principal_outstanding_inr: number;
  interest_rate_pct: number;
  min_monthly_payment_inr: number;
  due_day_of_month: number | null;
}

export async function listDebts(): Promise<DebtDTO[]> {
  return (await api.get<DebtDTO[]>('/debts')).data;
}

export async function createDebt(body: DebtInput): Promise<DebtDTO> {
  return (await api.post<DebtDTO>('/debts', body)).data;
}

export async function updateDebt(id: string, body: Partial<DebtInput> & { status?: 'active' | 'closed' }): Promise<DebtDTO> {
  return (await api.patch<DebtDTO>(`/debts/${id}`, body)).data;
}

export async function deleteDebt(id: string): Promise<void> {
  await api.delete(`/debts/${id}`);
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

export async function createGoal(body: GoalInput & { current_amount_inr?: number }): Promise<GoalDTO> {
  return (await api.post<GoalDTO>('/goals', body)).data;
}

export type GoalStatus = 'active' | 'paused' | 'completed' | 'cancelled';

export interface GoalDTO {
  id: string;
  title: string;
  category: string;
  target_amount_inr: number;
  current_amount_inr: number;
  progress_pct: number;
  target_date: ISODate | null;
  status: GoalStatus;
  projection: { monthly_rate_inr: number; projected_completion: ISODate | null; on_track: boolean | null };
}

export interface ContributionDTO {
  id: string;
  amount_inr: number;
  contributed_on: ISODate;
  note: string | null;
}

export interface GoalDetailDTO extends GoalDTO {
  contributions: ContributionDTO[];
}

/** "active" returns active and paused goals (S17 Active tab). */
export async function listGoals(status: 'active' | 'completed' | 'all' = 'active'): Promise<GoalDTO[]> {
  return (await api.get<GoalDTO[]>('/goals', { params: { status } })).data;
}

export async function getGoal(id: string): Promise<GoalDetailDTO> {
  return (await api.get<GoalDetailDTO>(`/goals/${id}`)).data;
}

export async function updateGoal(id: string, body: {
  title?: string; target_amount_inr?: number; target_date?: ISODate | null; status?: 'active' | 'paused' | 'cancelled';
}): Promise<GoalDTO> {
  return (await api.patch<GoalDTO>(`/goals/${id}`, body)).data;
}

export async function deleteGoal(id: string): Promise<void> {
  await api.delete(`/goals/${id}`);
}

/** Positive adds money, negative withdraws. */
export async function addContribution(id: string, amount: number, note: string | null): Promise<GoalDTO> {
  return (await api.post<GoalDTO>(`/goals/${id}/contributions`, { amount_inr: amount, note })).data;
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

export async function putEmergencyFund(targetMonths: number): Promise<EmergencyFundDTO> {
  return (await api.put<EmergencyFundDTO>('/plan/emergency-fund', { target_months: targetMonths })).data;
}

// --- Planner & risk (S12, S20, S21) ---------------------------------------------------

export type BudgetMode = 'lean' | 'normal' | 'surplus';
export type Confidence = 'low' | 'medium' | 'high';

export interface BudgetDTO {
  month: string;
  mode: BudgetMode;
  expected_income_inr: number;
  planning_income_inr: number;
  needs_limit_inr: number;
  wants_limit_inr: number;
  savings_target_inr: number;
  spent_needs_inr: number;
  spent_wants_inr: number;
  saved_so_far_inr: number;
  generated_at: string;
}

export interface ForecastMonthDTO {
  month: string;
  expected_income_inr: number;
  lower_income_inr: number;
  upper_income_inr: number;
  expected_expense_inr: number;
  expected_net_inr: number;
  mode: BudgetMode;
  confidence: Confidence;
}

export interface OverviewDTO {
  has_data: boolean;
  pattern: { label: 'steady' | 'ups_and_downs' | 'seasonal'; cv: number; months_of_data: number };
  income_history: { month: string; income_inr: number; is_lean: boolean }[];
  forecast: ForecastMonthDTO[];
  current_budget: BudgetDTO;
  emergency_fund: { exists: boolean; target_inr: number; current_inr: number; pct: number };
  tight_months: string[];
  data_confidence: Confidence;
}

export async function getOverview(): Promise<OverviewDTO> {
  return (await api.get<OverviewDTO>('/plan/overview')).data;
}

export async function regenerateBudget(): Promise<BudgetDTO> {
  return (await api.post<{ status: 'ok'; budget: BudgetDTO }>('/plan/budget/regenerate')).data.budget;
}

export type RiskKey = 'expense' | 'emergency' | 'volatility' | 'debt';

export interface RiskDTO {
  score: number;
  level: 'low' | 'medium' | 'high';
  computed_on: ISODate;
  components: { key: RiskKey; label: string; value: number; weight: number; tip: string; tip_key: string }[];
}

export async function getRisk(): Promise<RiskDTO> {
  return (await api.get<RiskDTO>('/risk/current')).data;
}

export async function getRiskHistory(days = 90): Promise<{ computed_on: ISODate; score: number; level: RiskDTO['level'] }[]> {
  return (await api.get('/risk/history', { params: { days } })).data;
}

// --- Chat (S22) & glossary term sheet --------------------------------------------------

export interface ChatMessageDTO {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  language: Language | null;
  input_mode: 'text' | 'voice';
  intent: string | null;
  highlighted_terms: TermSpan[];
  cards: ChatCardData[];
  suggested_replies: string[];
  mascot_pose: string | null;
  created_at: string;
}

export interface ChatReplyDTO {
  conversation_id: string;
  user_message: ChatMessageDTO;
  assistant_message: ChatMessageDTO;
  audio: { url: string; mime: 'audio/wav'; expires_in_sec: number } | null;
}

export async function sendChatMessage(text: string, conversationId: string | null): Promise<ChatReplyDTO> {
  // A reply can take several LLM calls (routing, answer, retries on a busy model): allow 2 minutes.
  return (await api.post<ChatReplyDTO>('/chat/messages', {
    text, ...(conversationId ? { conversation_id: conversationId } : {}),
  }, { timeout: 120_000 })).data;
}

export interface VoiceReplyDTO extends ChatReplyDTO {
  transcript: string;
  detected_language: Language;
}

/** A recording for /chat/voice: a file URI on phones, a Blob in the browser. */
export type RecordedAudio = { uri: string; name: string; type: string } | { blob: Blob; name: string };

function audioForm(audio: RecordedAudio, fields: Record<string, string | null | undefined>): FormData {
  const form = new FormData();
  if ('blob' in audio) form.append('audio', audio.blob, audio.name);
  else form.append('audio', audio as unknown as Blob); // React Native reads {uri, name, type}
  for (const [k, v] of Object.entries(fields)) if (v) form.append(k, v);
  return form;
}

export async function sendVoiceMessage(audio: RecordedAudio, conversationId: string | null, language: Language): Promise<VoiceReplyDTO> {
  // Upload + speech-to-text on the server's CPU + the chat reply: allow 3 minutes.
  return (await api.post<VoiceReplyDTO>('/chat/voice', audioForm(audio, { conversation_id: conversationId, language }), {
    timeout: 180_000, headers: { 'Content-Type': 'multipart/form-data' },
  })).data;
}

/** Server speech for a reply; url null = no server voice for this language (Tamil): speak on the device. */
export async function textToSpeech(text: string, language: Language | null): Promise<{ url: string | null }> {
  return (await api.post<{ url: string | null }>('/chat/tts', { text: text.slice(0, 1000), ...(language ? { language } : {}) })).data;
}

export async function getGreeting(lang: Language): Promise<{ text: string; mascot_pose: string; suggested_replies: string[] }> {
  return (await api.get('/chat/greeting', { params: { lang } })).data;
}

export interface ConversationDTO {
  id: string;
  title: string | null;
  channel: string;
  last_message_at: string;
}

export async function listConversations(cursor?: string | null): Promise<Page<ConversationDTO>> {
  return (await api.get<Page<ConversationDTO>>('/chat/conversations', { params: cursor ? { cursor } : {} })).data;
}

/** Newest first (the API's order); 30 per page. */
export async function listChatMessages(conversationId: string, cursor?: string | null): Promise<Page<ChatMessageDTO>> {
  return (await api.get<Page<ChatMessageDTO>>(`/chat/conversations/${conversationId}/messages`, {
    params: cursor ? { cursor } : {},
  })).data;
}

export async function deleteConversation(id: string): Promise<void> {
  await api.delete(`/chat/conversations/${id}`);
}

export interface VideoDTO {
  url: string;
  duration_sec: number;
  thumbnail_url: string | null;
}

export interface TermDetailDTO {
  slug: string;
  term: string;
  term_en: string;
  category: string;
  language: Language;
  definition: string;
  example: string;
  analogy: string;
  key_takeaway: string;
  related: { slug: string; term: string }[];
  video: VideoDTO | null;
  translation_source: 'llm' | 'human' | null;
}

export async function getTerm(slug: string): Promise<TermDetailDTO> {
  return (await api.get<TermDetailDTO>(`/learn/terms/${slug}`)).data;
}

// --- Learn (S32–S34) -----------------------------------------------------------------

export type GlossaryCategory = 'basics' | 'investing' | 'savings' | 'insurance' | 'loans';
export type LessonCategory = 'basics' | 'investing' | 'savings' | 'insurance';

export interface TermListItemDTO {
  slug: string;
  term: string;
  category: GlossaryCategory;
  short: string;
}

export async function searchTerms(params: { q?: string; category?: GlossaryCategory; limit?: number }): Promise<TermListItemDTO[]> {
  const query: Record<string, string | number> = { limit: params.limit ?? 20 };
  if (params.q) query.q = params.q;
  if (params.category) query.category = params.category;
  return (await api.get<{ items: TermListItemDTO[] }>('/learn/terms', { params: query })).data.items;
}

export async function termFeedback(slug: string, helpful: boolean): Promise<void> {
  await api.post(`/learn/terms/${slug}/feedback`, { helpful });
}

export interface LessonListItemDTO {
  id: string;
  slug: string;
  category: LessonCategory;
  title: string;
  duration_min: number;
  difficulty: 'easy' | 'medium';
  xp_reward: number;
  completed: boolean;
}

export interface LessonDetailDTO extends LessonListItemDTO {
  body_md: string;
  language: Language;
  video: VideoDTO | null;
  translation_source: 'llm' | 'human' | null;
}

export interface LearnStatsDTO {
  xp: number;
  level: number;
  streak_days: number;
  longest_streak: number;
  completed_lessons: number;
  total_lessons: number;
}

export async function listLessons(category?: LessonCategory): Promise<LessonListItemDTO[]> {
  return (await api.get<LessonListItemDTO[]>('/learn/lessons', { params: category ? { category } : {} })).data;
}

export async function getLesson(id: string): Promise<LessonDetailDTO> {
  return (await api.get<LessonDetailDTO>(`/learn/lessons/${id}`)).data;
}

export async function completeLesson(id: string): Promise<{ xp_awarded: number; stats: { xp: number; level: number; streak_days: number } }> {
  return (await api.post(`/learn/lessons/${id}/complete`)).data;
}

export async function getLearnStats(): Promise<LearnStatsDTO> {
  return (await api.get<LearnStatsDTO>('/learn/stats')).data;
}

// --- Scheme Scout (S23–S27) --------------------------------------------------------------

export type MatchStatusDTO = 'eligible' | 'possibly_eligible' | 'not_eligible';
export type TrackingStatus = 'saved' | 'applied' | 'dismissed';

export interface SchemeCategoryDTO { slug: string; name: string; icon: string; count: number }

export interface SchemeSummaryDTO {
  id: string;
  slug: string;
  name: string;
  level: 'central' | 'state';
  state_code: string | null;
  category_slug: string;
  benefit_summary: string;
  match_status: MatchStatusDTO | null;
}

export interface MatchItemDTO {
  scheme: SchemeSummaryDTO;
  status: MatchStatusDTO;
  missing_fields: string[];
  reasons: { rule_key: string; field: string; explanation: string }[];
}

export interface MatchesDTO { eligible_count: number; possibly_eligible_count: number; total: number; items: MatchItemDTO[] }

export interface QuestionDTO { field: string; type: 'boolean' | 'number' | 'enum'; options: string[] | null; affects_count: number }

export interface SchemeDetailDTO {
  scheme: SchemeSummaryDTO & {
    ministry_or_dept: string | null;
    benefit_type: string;
    description: string;
    application_mode: string | null;
    official_url: string;
    last_verified_on: ISODate;
    deadline_on: ISODate | null;
    translation_source: 'llm' | 'human' | null;
  };
  match: { status: MatchStatusDTO; rules: { rule_key: string; field: string; result: 'pass' | 'fail' | 'unknown'; explanation: string }[] };
  steps: { step_no: number; title: string; description: string }[];
  documents: { name: string; is_mandatory: boolean }[];
  tracking_status: TrackingStatus | null;
  language: Language;
  disclaimer: string;
}

export async function getSchemeCategories(): Promise<SchemeCategoryDTO[]> {
  return (await api.get<SchemeCategoryDTO[]>('/schemes/categories')).data;
}

export async function listSchemes(params: { category?: string; q?: string; status?: MatchStatusDTO; cursor?: string | null }): Promise<Page<SchemeSummaryDTO>> {
  const query: Record<string, string> = {};
  for (const [k, v] of Object.entries(params)) if (v) query[k] = v;
  return (await api.get<Page<SchemeSummaryDTO>>('/schemes', { params: query })).data;
}

export async function getSchemeMatches(): Promise<MatchesDTO> {
  return (await api.get<MatchesDTO>('/schemes/matches')).data;
}

export async function getEligibilityQuestions(): Promise<QuestionDTO[]> {
  return (await api.get<{ questions: QuestionDTO[] }>('/schemes/eligibility/questions')).data.questions;
}

/** null = "Not sure" (not saved). */
export async function checkEligibility(answers: Record<string, boolean | number | string | null>): Promise<MatchesDTO> {
  return (await api.post<MatchesDTO>('/schemes/eligibility/check', { answers })).data;
}

export async function getScheme(id: string): Promise<SchemeDetailDTO> {
  // The first open in hi/mr/ta may wait for a translation to be written.
  return (await api.get<SchemeDetailDTO>(`/schemes/${id}`, { timeout: 120_000 })).data;
}

export async function setSchemeTracking(id: string, status: TrackingStatus | null): Promise<void> {
  await api.put(`/schemes/${id}/tracking`, { status });
}

// --- Fraud Shield (S28–S31) -------------------------------------------------------------

export type Verdict = 'safe' | 'suspicious' | 'dangerous';
export type SourceApp = 'whatsapp' | 'sms' | 'other';

export interface FraudCheckDTO {
  id: string;
  input_type: 'text' | 'screenshot' | 'shared_text';
  source_app: SourceApp;
  snippet: string;
  risk_score: number;
  verdict: Verdict;
  summary: string;
  advice: string;
  reasons: { code: string; key: string; title: string; text: string }[];
  similar_reports_count: number;
  reported: boolean;
  language: Language;
  created_at: string;
}

export interface FraudCheckItemDTO {
  id: string;
  snippet: string;
  source_app: SourceApp;
  input_type: FraudCheckDTO['input_type'];
  verdict: Verdict;
  risk_score: number;
  created_at: string;
}

export async function analyzeText(text: string, sourceApp: SourceApp, language: Language): Promise<FraudCheckDTO> {
  return (await api.post<FraudCheckDTO>('/fraud/analyze/text', { text, source_app: sourceApp, language }, { timeout: 120_000 })).data;
}

/** A screenshot: a file URI on phones, a Blob in the browser. */
export type PickedImage = { uri: string; name: string; type: string } | { blob: Blob; name: string };

export async function analyzeImage(image: PickedImage, sourceApp: SourceApp, language: Language): Promise<FraudCheckDTO> {
  const form = new FormData();
  if ('blob' in image) form.append('image', image.blob, image.name);
  else form.append('image', image as unknown as Blob);
  form.append('source_app', sourceApp);
  form.append('language', language);
  return (await api.post<FraudCheckDTO>('/fraud/analyze/image', form, {
    timeout: 120_000, headers: { 'Content-Type': 'multipart/form-data' },
  })).data;
}

export async function listFraudChecks(cursor?: string | null): Promise<Page<FraudCheckItemDTO>> {
  return (await api.get<Page<FraudCheckItemDTO>>('/fraud/checks', { params: cursor ? { cursor } : {} })).data;
}

export async function getFraudCheck(id: string): Promise<FraudCheckDTO> {
  return (await api.get<FraudCheckDTO>(`/fraud/checks/${id}`)).data;
}

export async function deleteFraudCheck(id: string): Promise<void> {
  await api.delete(`/fraud/checks/${id}`);
}

export async function reportFraudCheck(id: string): Promise<{ reported: boolean }> {
  return (await api.post<{ reported: boolean }>(`/fraud/checks/${id}/report`)).data;
}

// --- Insights & notifications (S11, S13), push tokens ---------------------------------------

export interface InsightDTO {
  id: string;
  code: string;
  tone: 'info' | 'warning' | 'positive';
  filter_group: string;
  title: string;
  body: string;
  cta_route: string | null;
  is_read: boolean;
  language: Language;
  payload: Record<string, unknown> | null;
  created_at: string;
}

export type InsightFilter = 'all' | 'savings' | 'spending' | 'goals';

export async function listInsights(filter: InsightFilter, cursor?: string | null): Promise<Page<InsightDTO>> {
  return (await api.get<Page<InsightDTO>>('/insights', { params: { filter, ...(cursor ? { cursor } : {}) } })).data;
}

export async function markInsightRead(id: string): Promise<void> {
  await api.post(`/insights/${id}/read`);
}

export interface NotificationDTO {
  id: string;
  kind: string;
  title: string;
  body: string;
  data: { route?: string } | null;
  read: boolean;
  created_at: string;
}

export async function listNotifications(cursor?: string | null): Promise<Page<NotificationDTO>> {
  return (await api.get<Page<NotificationDTO>>('/notifications', { params: cursor ? { cursor } : {} })).data;
}

export async function markNotificationRead(id: string): Promise<void> {
  await api.post(`/notifications/${id}/read`);
}

export async function markAllNotificationsRead(): Promise<void> {
  await api.post('/notifications/read-all');
}

export async function registerDeviceToken(token: string, platform: 'android' | 'ios'): Promise<{ id: string }> {
  return (await api.post<{ id: string }>('/me/device-tokens', { expo_push_token: token, platform })).data;
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
