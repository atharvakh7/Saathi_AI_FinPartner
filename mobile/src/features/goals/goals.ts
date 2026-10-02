/** Goals (S17–S19): query keys, refresh after writes, form rules and projection wording. Pure, testable. */
import type { GoalDTO } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import { parseApiDate } from '@/lib/format';

export const goalKeys = {
  list: (status: 'active' | 'completed') => ['goals', 'list', status] as const,
  detail: (id: string) => ['goals', 'detail', id] as const,
  templates: ['goals', 'templates'] as const,
};

/** Goals feed Home (count, top goals, emergency fund %) and the planner. */
export function invalidateGoals(): void {
  for (const key of ['goals', 'summary', 'plan', 'emergency', 'risk', 'insights']) {
    void queryClient.invalidateQueries({ queryKey: [key] });
  }
}

export const MAX_GOAL_AMOUNT = 100_000_000;

export interface GoalFormValues {
  category: string | null;
  title: string;
  target: number | null;
  hasDate: boolean;
  targetDate: string; // YYYY-MM-DD, used when hasDate
  saved: number | null; // starting amount, create only
}

type GoalField = 'category' | 'title' | 'target' | 'targetDate' | 'saved';

export function validateGoal(v: GoalFormValues, today: string): Partial<Record<GoalField, string>> {
  const e: Partial<Record<GoalField, string>> = {};
  if (!v.category) e.category = 'goals.form.pickCategory';
  const title = v.title.trim();
  if (title.length < 2 || title.length > 80) e.title = 'form.nameLength';
  if (v.target === null || !(v.target > 0)) e.target = 'onboarding.goals.targetRequired';
  else if (v.target > MAX_GOAL_AMOUNT) e.target = 'finance.form.amountTooLarge';
  if (v.hasDate && !(v.targetDate > today)) e.targetDate = 'goals.form.dateFuture';
  if (v.saved !== null && (v.saved < 0 || v.saved > MAX_GOAL_AMOUNT)) e.saved = 'finance.form.amountTooLarge';
  return e;
}

/** Whole months from today to a target date (at least 1). */
export function monthsUntil(target: string, now: Date = new Date()): number {
  const d = parseApiDate(target);
  const months = (d.getFullYear() - now.getFullYear()) * 12 + (d.getMonth() - now.getMonth());
  return Math.max(1, months);
}

/** Amount per month still needed to finish by the target date, rounded up to ₹10. */
export function neededPerMonth(goal: Pick<GoalDTO, 'target_amount_inr' | 'current_amount_inr' | 'target_date'>, now = new Date()): number | null {
  if (!goal.target_date) return null;
  const left = goal.target_amount_inr - goal.current_amount_inr;
  if (left <= 0) return 0;
  return Math.ceil(left / monthsUntil(goal.target_date, now) / 10) * 10;
}

export type ProjectionMessage =
  | { key: 'goals.proj.done' }
  | { key: 'goals.proj.paused' }
  | { key: 'goals.proj.onTrack'; date: string }
  | { key: 'goals.proj.behind'; amount: number; date: string }
  | { key: 'goals.proj.atPace'; date: string; rate: number }
  | { key: 'goals.proj.start' };

/** Which sentence S18 shows under the ring. */
export function projectionMessage(g: GoalDTO, now = new Date()): ProjectionMessage {
  if (g.status === 'completed') return { key: 'goals.proj.done' };
  if (g.status === 'paused') return { key: 'goals.proj.paused' };
  const p = g.projection;
  if (g.target_date && p.on_track) return { key: 'goals.proj.onTrack', date: g.target_date };
  if (g.target_date && p.on_track === false) return { key: 'goals.proj.behind', amount: neededPerMonth(g, now) ?? 0, date: g.target_date };
  if (p.projected_completion && p.monthly_rate_inr > 0) return { key: 'goals.proj.atPace', date: p.projected_completion, rate: p.monthly_rate_inr };
  return { key: 'goals.proj.start' };
}
