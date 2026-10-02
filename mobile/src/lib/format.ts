/**
 * Money and dates (spec §4.1): ₹ with Indian digit grouping; dates shown as DD MMM YYYY, sent as YYYY-MM-DD.
 * Implemented by hand rather than with Intl: Hermes' Intl support for 'en-IN' grouping varies by device.
 */

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** 124000 -> "1,24,000"; 1234.5 -> "1,234.50"; negative numbers keep their sign. */
export function groupIndian(value: number, decimals: 0 | 2 | 'auto' = 'auto'): string {
  const negative = value < 0;
  const abs = Math.abs(value);
  const showPaise = decimals === 2 || (decimals === 'auto' && Math.round(abs * 100) % 100 !== 0);
  const fixed = abs.toFixed(showPaise ? 2 : 0);
  const [whole = '0', frac] = fixed.split('.');
  let grouped = whole;
  if (whole.length > 3) {
    const tail = whole.slice(-3);
    let head = whole.slice(0, -3);
    const groups: string[] = [];
    while (head.length > 2) {
      groups.unshift(head.slice(-2));
      head = head.slice(0, -2);
    }
    if (head) groups.unshift(head);
    grouped = `${groups.join(',')},${tail}`;
  }
  return `${negative ? '-' : ''}${grouped}${frac ? `.${frac}` : ''}`;
}

export function inr(value: number | null | undefined, decimals: 0 | 2 | 'auto' = 'auto'): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '₹–';
  return value < 0 ? `-₹${groupIndian(-value, decimals)}` : `₹${groupIndian(value, decimals)}`;
}

/** Parse what a user typed in an amount field: "1,24,000" / "1240.5" -> number, else null. */
export function parseAmount(text: string): number | null {
  const cleaned = text.replace(/[₹,\s]/g, '');
  if (!/^\d+(\.\d{1,2})?$/.test(cleaned)) return null;
  const n = Number(cleaned);
  return Number.isFinite(n) ? n : null;
}

/** "2026-09-30" or a Date -> "30 Sep 2026". Dates without a time are read as calendar dates (no TZ shift). */
export function displayDate(value: string | Date | null | undefined): string {
  if (!value) return '';
  if (typeof value === 'string') {
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
    if (m && value.length === 10) return `${m[3]} ${MONTHS[Number(m[2]) - 1]} ${m[1]}`;
    value = new Date(value);
  }
  if (Number.isNaN(value.getTime())) return '';
  return `${String(value.getDate()).padStart(2, '0')} ${MONTHS[value.getMonth()]} ${value.getFullYear()}`;
}

/** Local calendar date -> "YYYY-MM-DD". */
export function apiDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

/** "2026-09" -> "Sep 2026". */
export function displayMonth(ym: string): string {
  const m = /^(\d{4})-(\d{2})$/.exec(ym);
  return m ? `${MONTHS[Number(m[2]) - 1]} ${m[1]}` : ym;
}

/** Local month -> "YYYY-MM". */
export function apiMonth(d: Date = new Date()): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

/** "2026-09" + 1 -> "2026-10"; "2026-01" - 1 -> "2025-12". */
export function shiftMonth(ym: string, delta: number): string {
  const [y, m] = ym.split('-').map(Number) as [number, number];
  const index = y * 12 + (m - 1) + delta;
  return `${Math.floor(index / 12)}-${String((index % 12) + 1).padStart(2, '0')}`;
}

/** "YYYY-MM-DD" -> Date at local midnight (no TZ shift). */
export function parseApiDate(value: string): Date {
  const [y, m, d] = value.slice(0, 10).split('-').map(Number) as [number, number, number];
  return new Date(y, m - 1, d);
}

/** Weeks of the month as rows of 7 cells (Sunday first); null = padding. */
export function monthGrid(ym: string): (string | null)[][] {
  const [y, m] = ym.split('-').map(Number) as [number, number];
  const first = new Date(y, m - 1, 1).getDay();
  const days = new Date(y, m, 0).getDate();
  const cells: (string | null)[] = Array.from({ length: first }, () => null);
  for (let d = 1; d <= days; d++) cells.push(`${ym}-${String(d).padStart(2, '0')}`);
  while (cells.length % 7) cells.push(null);
  const rows: (string | null)[][] = [];
  for (let i = 0; i < cells.length; i += 7) rows.push(cells.slice(i, i + 7));
  return rows;
}

/** Today / Yesterday / "30 Sep 2026" for list headers: returns an i18n key or the formatted date. */
export function dayLabel(value: string, now: Date = new Date()): { key?: 'common.today' | 'common.yesterday'; text: string } {
  const today = apiDate(now);
  const y = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
  if (value === today) return { key: 'common.today', text: displayDate(value) };
  if (value === apiDate(y)) return { key: 'common.yesterday', text: displayDate(value) };
  return { text: displayDate(value) };
}

/** "2026-09" -> "Sep" (chart axis labels). */
export function shortMonth(ym: string): string {
  return MONTHS[Number(ym.slice(5, 7)) - 1] ?? ym;
}

/** Compact rupees for chart labels: 1500 -> "₹1.5k", 240000 -> "₹2.4L". */
export function inrShort(value: number): string {
  const abs = Math.abs(value);
  const sign = value < 0 ? '-' : '';
  const trim = (n: number) => String(Number(n.toFixed(1)));
  if (abs >= 1e7) return `${sign}₹${trim(abs / 1e7)}Cr`;
  if (abs >= 1e5) return `${sign}₹${trim(abs / 1e5)}L`;
  if (abs >= 1e3) return `${sign}₹${trim(abs / 1e3)}k`;
  return `${sign}₹${Math.round(abs)}`;
}

/** Minutes/hours/days ago, for lists; returns [i18n key, count]. */
export function relativeTime(iso: string, now: Date = new Date()): [string, number] {
  const seconds = Math.max(0, (now.getTime() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return ['time.justNow', 0];
  if (seconds < 3600) return ['time.minutesAgo', Math.floor(seconds / 60)];
  if (seconds < 86400) return ['time.hoursAgo', Math.floor(seconds / 3600)];
  return ['time.daysAgo', Math.floor(seconds / 86400)];
}
