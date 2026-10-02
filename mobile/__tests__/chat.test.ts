import type { ChatMessageDTO, ChatReplyDTO } from '@/api/endpoints';
import { cardAction, changesMoneyData, withReply } from '@/features/chat/chat';

const msg = (id: string, role: 'user' | 'assistant'): ChatMessageDTO => ({
  id, role, content: id, language: 'en', input_mode: 'text', intent: null, highlighted_terms: [], cards: [],
  suggested_replies: [], mascot_pose: null, created_at: '2026-10-02T10:00:00Z',
});
const reply = (u: string, a: string): ChatReplyDTO => ({ conversation_id: 'c', user_message: msg(u, 'user'), assistant_message: msg(a, 'assistant'), audio: null });

test('a reply goes to the top of the newest-first pages, once', () => {
  const first = withReply(undefined, reply('u1', 'a1'));
  expect(first.pages[0]!.items.map((m) => m.id)).toEqual(['a1', 'u1']);
  const second = withReply(first, reply('u2', 'a2'));
  expect(second.pages[0]!.items.map((m) => m.id)).toEqual(['a2', 'u2', 'a1', 'u1']);
  expect(withReply(second, reply('u2', 'a2')).pages[0]!.items).toHaveLength(4); // no duplicates
});

test('card taps: terms open the sheet, ready routes navigate, others wait', () => {
  expect(cardAction({ type: 'term', payload: { slug: 'sip', term: 'SIP', definition: '', key_takeaway: '' } }, '/term/sip'))
    .toEqual({ kind: 'term', slug: 'sip' });
  const goal = { type: 'goal', payload: { id: 'g', title: '', target_amount_inr: 1, current_amount_inr: 0, progress_pct: 0, target_date: null } } as const;
  expect(cardAction(goal, '/goals/g')).toEqual({ kind: 'route', route: '/goals/g' });
  expect(cardAction(goal, '/plan')).toEqual({ kind: 'route', route: '/plan' });
  expect(cardAction(goal, '/schemes/x')).toEqual({ kind: 'route', route: '/schemes/x' });
  expect(cardAction(goal, '/somewhere/else')).toEqual({ kind: 'soon' });
  expect(cardAction(goal)).toBeNull();
});

test('replies that may have saved money data refresh Home', () => {
  expect(changesMoneyData('log_transaction')).toBe(true);
  expect(changesMoneyData('goal_action')).toBe(true);
  expect(changesMoneyData('jargon_explain')).toBe(false);
  expect(changesMoneyData(null)).toBe(false);
});
