/** Saathi chat (S22): query keys, cache updates after a reply, where cards open. Pure where possible. */
import type { InfiniteData } from '@tanstack/react-query';

import type { ChatMessageDTO, ChatReplyDTO } from '@/api/endpoints';
import type { Page } from '@/api/types';
import type { ChatCardData } from '@/components/chat';

export const chatKeys = {
  conversations: ['chat', 'conversations'] as const,
  messages: (id: string) => ['chat', 'messages', id] as const,
  greeting: (lang: string) => ['chat', 'greeting', lang] as const,
  term: (slug: string, lang: string) => ['term', slug, lang] as const,
};

type Pages = InfiniteData<Page<ChatMessageDTO>, string | null>;

/** Put a new exchange at the top of the newest-first message pages (no refetch, no duplicates). */
export function withReply(data: Pages | undefined, reply: ChatReplyDTO): Pages {
  const fresh = [reply.assistant_message, reply.user_message];
  if (!data || data.pages.length === 0) {
    return { pages: [{ items: fresh, next_cursor: null }], pageParams: [null] };
  }
  const ids = new Set(fresh.map((m) => m.id));
  const [first, ...rest] = data.pages;
  return {
    ...data,
    pages: [{ ...first!, items: [...fresh, ...first!.items.filter((m) => !ids.has(m.id))] }, ...rest],
  };
}

/** Routes that exist so far; cards pointing elsewhere aren't opened yet. */
const READY = [/^\/goals\//, /^\/plan$/, /^\/term\//, /^\/schemes\//, /^\/fraud\//];

export type CardAction = { kind: 'term'; slug: string } | { kind: 'route'; route: string } | { kind: 'soon' } | null;

export function cardAction(card: ChatCardData, route?: string): CardAction {
  if (card.type === 'term') return { kind: 'term', slug: card.payload.slug };
  if (!route) return null;
  return READY.some((r) => r.test(route)) ? { kind: 'route', route } : { kind: 'soon' };
}

/** Intents whose reply may have saved money data (the transaction / goal confirmation flows). */
export function changesMoneyData(intent: string | null): boolean {
  return !!intent && /transaction|goal|confirm/.test(intent);
}

/** "14:05" in the device's local time. */
export function clockTime(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '' : `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}
