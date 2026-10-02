import type { GoalDTO } from '@/api/endpoints';
import { monthsUntil, neededPerMonth, projectionMessage, validateGoal, type GoalFormValues } from '@/features/goals/goals';

const now = new Date(2026, 9, 2); // 2 Oct 2026

const goal = (g: Partial<GoalDTO> = {}): GoalDTO => ({
  id: 'g', title: 'Bike', category: 'vehicle', target_amount_inr: 60000, current_amount_inr: 24000, progress_pct: 40,
  target_date: '2027-04-02', status: 'active',
  projection: { monthly_rate_inr: 0, projected_completion: null, on_track: null }, ...g,
});

test('months and amount needed per month', () => {
  expect(monthsUntil('2027-04-02', now)).toBe(6);
  expect(monthsUntil('2026-10-20', now)).toBe(1); // never 0
  expect(neededPerMonth(goal(), now)).toBe(6000); // 36,000 left / 6 months
  expect(neededPerMonth(goal({ target_amount_inr: 60001 }), now)).toBe(6010); // rounded up to ₹10
  expect(neededPerMonth(goal({ target_date: null }), now)).toBeNull();
  expect(neededPerMonth(goal({ current_amount_inr: 60000 }), now)).toBe(0);
});

test('projection sentence for S18', () => {
  expect(projectionMessage(goal({ status: 'completed' }), now).key).toBe('goals.proj.done');
  expect(projectionMessage(goal({ status: 'paused' }), now).key).toBe('goals.proj.paused');
  expect(projectionMessage(goal({ projection: { monthly_rate_inr: 7000, projected_completion: '2027-03-01', on_track: true } }), now))
    .toEqual({ key: 'goals.proj.onTrack', date: '2027-04-02' });
  expect(projectionMessage(goal({ projection: { monthly_rate_inr: 1000, projected_completion: '2029-06-01', on_track: false } }), now))
    .toEqual({ key: 'goals.proj.behind', amount: 6000, date: '2027-04-02' });
  expect(projectionMessage(goal({ target_date: null, projection: { monthly_rate_inr: 2000, projected_completion: '2028-01-01', on_track: null } }), now))
    .toEqual({ key: 'goals.proj.atPace', date: '2028-01-01', rate: 2000 });
  expect(projectionMessage(goal({ target_date: null }), now).key).toBe('goals.proj.start');
});

const form = (v: Partial<GoalFormValues> = {}): GoalFormValues => ({
  category: 'vehicle', title: 'Bike', target: 60000, hasDate: false, targetDate: '2027-04-02', saved: null, ...v,
});

test('goal form rules match the API (S19)', () => {
  const today = '2026-10-02';
  expect(validateGoal(form(), today)).toEqual({});
  expect(validateGoal(form({ category: null }), today).category).toBe('goals.form.pickCategory');
  expect(validateGoal(form({ title: ' B ' }), today).title).toBe('form.nameLength');
  expect(validateGoal(form({ target: 0 }), today).target).toBe('onboarding.goals.targetRequired');
  expect(validateGoal(form({ target: 100_000_001 }), today).target).toBe('finance.form.amountTooLarge');
  expect(validateGoal(form({ hasDate: true, targetDate: today }), today).targetDate).toBe('goals.form.dateFuture');
  expect(validateGoal(form({ hasDate: true, targetDate: '2026-10-03' }), today)).toEqual({});
  expect(validateGoal(form({ hasDate: false, targetDate: today }), today)).toEqual({}); // date ignored when off
});
