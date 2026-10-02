/** Tap on an insight: mark it read and open its screen (kept apart so insights.ts stays testable). */
import { router } from 'expo-router';

import { markInsightRead, type InsightDTO } from '@/api/endpoints';
import { appRoute } from '@/lib/routes';
import { invalidateInbox } from './insights';

export function openInsight(i: InsightDTO): void {
  if (!i.is_read) void markInsightRead(i.id).then(invalidateInbox).catch(() => undefined);
  const route = appRoute(i.cta_route);
  if (route) router.push(route as never);
}
