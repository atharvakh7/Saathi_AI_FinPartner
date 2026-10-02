/** Voice (step 26): pure helpers for recording limits, upload naming and on-device speech. */
import type { Language } from '@/i18n';

/** The API rejects recordings over 60 s (413); stop a little before that. */
export const MAX_RECORDING_SEC = 59;
/** Shorter than this is almost always an accidental tap. */
export const MIN_RECORDING_SEC = 1;

/** File name + MIME type the API accepts for what this platform records. */
export function uploadMeta(platform: string): { name: string; type: string } {
  return platform === 'web' ? { name: 'voice.webm', type: 'audio/webm' } : { name: 'voice.m4a', type: 'audio/m4a' };
}

/** BCP-47 tag for expo-speech (used for Tamil, which has no server voice, and as a fallback). */
export function speechLanguage(lang: Language | null | undefined): string {
  switch (lang) {
    case 'hi': return 'hi-IN';
    case 'mr': return 'mr-IN';
    case 'ta': return 'ta-IN';
    default: return 'en-IN';
  }
}

/** "0:07 / 0:59" style timer text. */
export function clock(sec: number): string {
  const s = Math.max(0, Math.floor(sec));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}
