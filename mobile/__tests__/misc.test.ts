import { execFileSync } from 'child_process';
import path from 'path';

import type { MeDTO } from '@/api/types';
import { splitHighlights } from '@/lib/highlight';
import { routeForSession } from '@/lib/routing';

const me = (needs: MeDTO['needs'], done: string | null): MeDTO => ({
  user: {
    id: 'u', phone_masked: '+91 ••••• 43210', role: 'user', preferred_language: 'hi', voice_reply_enabled: true,
    onboarding_completed_at: done, first_name: 'Ramesh',
  },
  profile: null,
  needs,
});

test('session routing (auth guard)', () => {
  expect(routeForSession(false, null)).toBe('/onboarding/welcome');
  expect(routeForSession(true, me('consent', null))).toBe('/onboarding/consent');
  expect(routeForSession(true, me('confidence', null))).toBe('/onboarding/confidence');
  expect(routeForSession(true, me(null, '2026-09-30T10:00:00Z'))).toBe('/home');
});

test('highlighted terms split by UTF-16 offsets, bad spans ignored', () => {
  const text = 'SIP म्हणजे mutual fund 😀 EMI';
  const emi = text.indexOf('EMI');
  const parts = splitHighlights(text, [
    { slug: 'sip', surface: 'SIP', start: 0, end: 3 },
    { slug: 'emi', surface: 'EMI', start: emi, end: emi + 3 },
    { slug: 'bad', surface: 'x', start: 1, end: 2 }, // overlaps SIP
  ]);
  expect(parts.filter((p) => p.slug).map((p) => p.text)).toEqual(['SIP', 'EMI']);
  expect(parts.map((p) => p.text).join('')).toBe(text);
});

test('i18n files have identical keys and placeholders in all four languages', () => {
  const out = execFileSync('node', [path.join(__dirname, '..', 'scripts', 'check-i18n.js')]).toString();
  expect(out).toMatch(/i18n OK/);
});
