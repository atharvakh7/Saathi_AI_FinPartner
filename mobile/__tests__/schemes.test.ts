import type { MatchItemDTO } from '@/api/endpoints';
import { groupMatches, nextQuestion, numberAnswer, optionKey } from '@/features/schemes/schemes';

test('number answers are whole numbers only (the API is strict)', () => {
  expect(numberAnswer('1,50,000')).toBe(150000);
  expect(numberAnswer('₹ 2000')).toBe(2000);
  expect(numberAnswer('12.5')).toBeNull();
  expect(numberAnswer('')).toBeNull();
  expect(numberAnswer('abc')).toBeNull();
});

test('enum answers reuse the profile option labels', () => {
  expect(optionKey('gender', 'female')).toBe('options.gender.female');
  expect(optionKey('area_type', 'rural')).toBe('options.area.rural');
  expect(optionKey('social_category', 'sc')).toBe('options.social.sc');
  expect(optionKey('state_code', 'MH')).toBe('state.MH');
});

test('matches grouped for S25 and the next unanswered question', () => {
  const m = (id: string, status: MatchItemDTO['status']) => ({ status, missing_fields: [], reasons: [], scheme: { id } }) as unknown as MatchItemDTO;
  const g = groupMatches([m('a', 'eligible'), m('b', 'not_eligible'), m('c', 'possibly_eligible'), m('d', 'eligible')]);
  expect([g.eligible.length, g.possibly.length, g.not.length]).toEqual([2, 1, 1]);
  const qs = [{ field: 'age_years', type: 'number', options: null, affects_count: 3 }, { field: 'is_student', type: 'boolean', options: null, affects_count: 2 }] as const;
  expect(nextQuestion([...qs], {})?.field).toBe('age_years');
  expect(nextQuestion([...qs], { age_years: 30 })?.field).toBe('is_student');
  expect(nextQuestion([...qs], { age_years: 30, is_student: null })).toBeNull(); // "Not sure" counts as answered
});
