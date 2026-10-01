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

/** Minutes/hours/days ago, for lists; returns [i18n key, count]. */
export function relativeTime(iso: string, now: Date = new Date()): [string, number] {
  const seconds = Math.max(0, (now.getTime() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return ['time.justNow', 0];
  if (seconds < 3600) return ['time.minutesAgo', Math.floor(seconds / 60)];
  if (seconds < 86400) return ['time.hoursAgo', Math.floor(seconds / 3600)];
  return ['time.daysAgo', Math.floor(seconds / 86400)];
}
