import type { TermListItemDTO } from '@/api/endpoints';
import { lessonProgress, popularTerms, xpToNextLevel } from '@/features/learn/learn';

test('popular terms keep the wireframe order and skip missing ones', () => {
  const t = (slug: string): TermListItemDTO => ({ slug, term: slug.toUpperCase(), category: 'basics', short: '' });
  expect(popularTerms([t('nav'), t('sip'), t('emi'), t('budget')]).map((x) => x.slug)).toEqual(['emi', 'sip', 'nav']);
});

test('progress and level maths (API: level = max(1, xp // 100))', () => {
  expect(lessonProgress(3, 12)).toBe(25);
  expect(lessonProgress(0, 0)).toBe(0);
  expect(xpToNextLevel(0)).toBe(200); // level 1 until 200 XP
  expect(xpToNextLevel(150)).toBe(50);
  expect(xpToNextLevel(230)).toBe(70); // level 2 -> 300
});
