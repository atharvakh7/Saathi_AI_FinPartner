/** Highlighted glossary terms in chat text (spans come from the API in UTF-16 offsets). */

export interface TermSpan {
  slug: string;
  surface: string;
  start: number; // UTF-16 offsets — the same units JavaScript strings use
  end: number;
}

/** Split text into plain and highlighted parts; overlapping or out-of-range spans are ignored. */
export function splitHighlights(text: string, spans: TermSpan[]): { text: string; slug?: string }[] {
  const parts: { text: string; slug?: string }[] = [];
  let pos = 0;
  for (const s of [...spans].sort((a, b) => a.start - b.start)) {
    if (s.start < pos || s.end > text.length || s.end <= s.start) continue;
    if (s.start > pos) parts.push({ text: text.slice(pos, s.start) });
    parts.push({ text: text.slice(s.start, s.end), slug: s.slug });
    pos = s.end;
  }
  if (pos < text.length) parts.push({ text: text.slice(pos) });
  return parts;
}
