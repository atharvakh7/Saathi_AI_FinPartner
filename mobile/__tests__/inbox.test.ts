import type { InsightDTO } from '@/api/endpoints';
import { insightText } from '@/features/insights/insights';
import { appRoute } from '@/lib/routes';

test('API routes from insights/notifications map to app screens', () => {
  expect(appRoute('/transactions')).toBe('/finance/transactions');
  expect(appRoute('/transactions/new')).toBe('/finance/transaction?type=income');
  expect(appRoute('/plan/emergency-fund')).toBe('/emergency-fund');
  expect(appRoute('/schemes/results')).toBe('/schemes/matches');
  expect(appRoute('/goals/0b9a1c2d-1111-4222-8333-444455556666')).toBe('/goals/0b9a1c2d-1111-4222-8333-444455556666');
  expect(appRoute('/schemes/0b9a1c2d-1111-4222-8333-444455556666')).toBe('/schemes/0b9a1c2d-1111-4222-8333-444455556666');
  expect(appRoute('/insights')).toBe('/insights');
  expect(appRoute('/learn/term/sip')).toBe('/term/sip');
  expect(appRoute('/plan/')).toBe('/plan');
  expect(appRoute('/nowhere')).toBeNull();
  expect(appRoute(null)).toBeNull();
});

const insight = (lang: 'en' | 'hi'): InsightDTO => ({
  id: 'i', code: 'I02', tone: 'positive', filter_group: 'savings', title: 'Server title', body: 'Server body', cta_route: '/plan',
  is_read: false, language: lang, payload: { amt: 1200, months: ['2026-11', '2026-12'] }, created_at: '2026-10-02T00:00:00Z',
});

test('insight wording: server text in the UI language, else the app translation with the numbers', () => {
  const t = (k: string, v?: Record<string, unknown>) => `${k}|${JSON.stringify(v)}`;
  const exists = () => true;
  expect(insightText(insight('hi'), 'hi', t, exists)).toEqual({ title: 'Server title', body: 'Server body' });
  const fallback = insightText(insight('en'), 'hi', t, exists);
  expect(fallback.title).toContain('insight.I02.title');
  expect(fallback.body).toContain('"amt":1200');
  expect(fallback.body).toContain('"months":"2026-11, 2026-12"');
  expect(insightText(insight('en'), 'hi', t, () => false).title).toBe('Server title'); // no app string -> server text
});
