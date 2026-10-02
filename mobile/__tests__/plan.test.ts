import { partLevel, riskContributions } from '@/features/plan/plan';
import { inrShort, shortMonth } from '@/lib/format';

test('risk parts add up to the score and sort biggest first (S12)', () => {
  // Backend: score = 5 × Σ weight × value
  const parts = riskContributions([
    { key: 'expense', label: '', value: 0.6, weight: 0.35, tip: '', tip_key: 'risk.tip.expense' },
    { key: 'emergency', label: '', value: 1, weight: 0.25, tip: '', tip_key: 'risk.tip.emergency' },
    { key: 'volatility', label: '', value: 0.1, weight: 0.2, tip: '', tip_key: 'risk.tip.volatility' },
    { key: 'debt', label: '', value: 0, weight: 0.2, tip: '', tip_key: 'risk.tip.debt' },
  ]);
  expect(parts.map((p) => p.key)).toEqual(['emergency', 'expense', 'volatility', 'debt']);
  expect(parts.map((p) => p.points)).toEqual([1.3, 1.1, 0.1, 0]);
  expect(partLevel(0.2)).toBe('low');
  expect(partLevel(0.5)).toBe('medium');
  expect(partLevel(0.9)).toBe('high');
});

test('chart labels', () => {
  expect(shortMonth('2026-09')).toBe('Sep');
  expect(inrShort(850)).toBe('₹850');
  expect(inrShort(1500)).toBe('₹1.5k');
  expect(inrShort(24000)).toBe('₹24k');
  expect(inrShort(240000)).toBe('₹2.4L');
  expect(inrShort(-12500)).toBe('-₹12.5k');
  expect(inrShort(30_000_000)).toBe('₹3Cr');
});
