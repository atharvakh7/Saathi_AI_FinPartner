import { apiDate, displayDate, displayMonth, groupIndian, inr, parseAmount, relativeTime } from '@/lib/format';

describe('Indian money format', () => {
  it.each([
    [0, '₹0'], [999, '₹999'], [1000, '₹1,000'], [124000, '₹1,24,000'], [10000000, '₹1,00,00,000'],
    [1234.5, '₹1,234.50'], [-2500, '-₹2,500'],
  ])('%p -> %p', (n, s) => expect(inr(n)).toBe(s));
  it('handles missing values', () => expect(inr(null)).toBe('₹–'));
  it('groups without symbol', () => expect(groupIndian(150000, 0)).toBe('1,50,000'));
  it('parses typed amounts', () => {
    expect(parseAmount('1,24,000')).toBe(124000);
    expect(parseAmount('₹ 1240.5')).toBe(1240.5);
    expect(parseAmount('12.345')).toBeNull();
    expect(parseAmount('abc')).toBeNull();
  });
});

describe('dates', () => {
  it('shows DD MMM YYYY without timezone shifts', () => expect(displayDate('2026-09-30')).toBe('30 Sep 2026'));
  it('sends YYYY-MM-DD', () => expect(apiDate(new Date(2026, 0, 5))).toBe('2026-01-05'));
  it('months', () => expect(displayMonth('2026-11')).toBe('Nov 2026'));
  it('relative time', () => {
    const now = new Date('2026-10-01T12:00:00Z');
    expect(relativeTime('2026-10-01T11:59:30Z', now)).toEqual(['time.justNow', 0]);
    expect(relativeTime('2026-10-01T11:15:00Z', now)).toEqual(['time.minutesAgo', 45]);
    expect(relativeTime('2026-09-29T12:00:00Z', now)).toEqual(['time.daysAgo', 2]);
  });
});
