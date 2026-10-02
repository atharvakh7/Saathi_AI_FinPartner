/** Learn (S32–S34): query keys, popular terms, small pure helpers. */
import { useEffect, useState } from 'react';

import type { TermListItemDTO } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';

export const learnKeys = {
  stats: ['learn', 'stats'] as const,
  terms: (lang: string, q: string) => ['learn', 'terms', lang, q] as const,
  term: (slug: string, lang: string) => ['term', slug, lang] as const, // shared with the chat's term sheet
  lessons: (lang: string, category: string) => ['learn', 'lessons', lang, category] as const,
  lesson: (id: string, lang: string) => ['learn', 'lesson', id, lang] as const,
};

/** The wireframe's "Popular Terms", most-asked first. */
export const POPULAR_TERMS = ['emi', 'sip', 'credit-score', 'nav', 'mutual-fund', 'upi', 'emergency-fund', 'inflation'];

/** Popular terms in display order, using the localized names from the term list. */
export function popularTerms(all: TermListItemDTO[]): TermListItemDTO[] {
  const bySlug = new Map(all.map((t) => [t.slug, t]));
  return POPULAR_TERMS.map((s) => bySlug.get(s)).filter((t): t is TermListItemDTO => !!t);
}

/** Lessons done out of total, as a whole percent. */
export function lessonProgress(done: number, total: number): number {
  return total > 0 ? Math.min(100, Math.round((100 * done) / total)) : 0;
}

/** XP still needed for the next level (the API: level = max(1, xp // 100)). */
export function xpToNextLevel(xp: number): number {
  const next = (Math.max(1, Math.floor(xp / 100)) + 1) * 100;
  return next - xp;
}

/** Learning activity (lesson done, term viewed) changes stats and streak. */
export function invalidateLearn(): void {
  void queryClient.invalidateQueries({ queryKey: ['learn'] });
}

export function useDebounced<T>(value: T, ms = 300): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), ms);
    return () => clearTimeout(id);
  }, [value, ms]);
  return v;
}
