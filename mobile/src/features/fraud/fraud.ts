/** Fraud Shield (S28–S31): query keys, verdict colours, input rules. Pure, testable. */
import type { Verdict } from '@/api/endpoints';
import type { Tone } from '@/theme';

export const fraudKeys = {
  checks: ['fraud', 'checks'] as const,
  check: (id: string) => ['fraud', 'check', id] as const,
};

/** The API accepts 10–5000 characters. */
export const MIN_TEXT = 10;
export const MAX_TEXT = 5000;
/** Screenshots: jpg / png / webp up to 5 MB. */
export const MAX_IMAGE_BYTES = 5 * 1024 * 1024;

export const VERDICT_TONE: Record<Verdict, Tone> = { safe: 'positive', suspicious: 'warning', dangerous: 'danger' };

export function textProblem(text: string): 'tooShort' | 'tooLong' | null {
  const n = text.trim().length;
  if (n < MIN_TEXT) return 'tooShort';
  if (n > MAX_TEXT) return 'tooLong';
  return null;
}

/** "image/png" etc. for an upload name; anything else is sent as jpeg (the API checks the bytes). */
export function imageMeta(uriOrName: string, mime?: string | null): { name: string; type: string } {
  const type = mime && /^image\/(jpeg|png|webp)$/.test(mime) ? mime
    : /\.png$/i.test(uriOrName) ? 'image/png' : /\.webp$/i.test(uriOrName) ? 'image/webp' : 'image/jpeg';
  const ext = type === 'image/png' ? 'png' : type === 'image/webp' ? 'webp' : 'jpg';
  return { name: `screenshot.${ext}`, type };
}
