/** Insights (S11) and notifications (S13): keys, wording, refresh. */
import type { InsightDTO } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import type { Language } from '@/i18n';

export const insightKeys = {
  list: (filter: string, lang: string) => ['insights', filter, lang] as const,
  notifications: ['notifications'] as const,
};

type T = (key: string, vars?: Record<string, unknown>) => string;

/** Payload values as text for the app's `insight.<code>` strings (lists joined). */
function vars(payload: Record<string, unknown> | null): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(payload ?? {})) out[k] = Array.isArray(v) ? v.join(', ') : v;
  return out;
}

/**
 * The server's text when it is already in the UI language; otherwise the app's own translation of
 * the insight code with the server's numbers (the server falls back to English when a rewrite fails).
 */
export function insightText(i: InsightDTO, ui: Language, t: T, exists: (key: string) => boolean): { title: string; body: string } {
  const key = `insight.${i.code}`;
  if (i.language === ui || !exists(`${key}.title`)) return { title: i.title, body: i.body };
  return { title: t(`${key}.title`, vars(i.payload)), body: t(`${key}.body`, vars(i.payload)) };
}

export function invalidateInbox(): void {
  for (const key of ['insights', 'notifications', 'summary']) void queryClient.invalidateQueries({ queryKey: [key] });
}

