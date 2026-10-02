/** Scheme Scout (S23–S27): query keys, refresh, answer labels. Pure where possible. */
import type { MatchItemDTO, QuestionDTO } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';

export const schemeKeys = {
  categories: ['schemes', 'categories'] as const,
  matches: (lang: string) => ['schemes', 'matches', lang] as const,
  questions: ['schemes', 'questions'] as const,
  list: (lang: string, category: string, q: string, status: string) => ['schemes', 'list', lang, category, q, status] as const,
  detail: (id: string, lang: string) => ['schemes', 'detail', id, lang] as const,
};

export function invalidateSchemes(): void {
  void queryClient.invalidateQueries({ queryKey: ['schemes'] });
  void queryClient.invalidateQueries({ queryKey: ['me'] }); // eligibility answers are saved to the profile
}

/** i18n key for an enum answer (reuses the profile option labels). */
export function optionKey(field: string, value: string): string {
  switch (field) {
    case 'gender': return `options.gender.${value}`;
    case 'area_type': return `options.area.${value}`;
    case 'occupation_type': return `options.occupation.${value}`;
    case 'social_category': return `options.social.${value}`;
    case 'state_code': return `state.${value}`;
    default: return value;
  }
}

/** Parse a typed number answer: whole numbers only (the API is strict). */
export function numberAnswer(text: string): number | null {
  const cleaned = text.replace(/[,\s₹]/g, '');
  return /^\d{1,12}$/.test(cleaned) ? Number(cleaned) : null;
}

/** Group matches the way S25 shows them. */
export function groupMatches(items: MatchItemDTO[]) {
  return {
    eligible: items.filter((m) => m.status === 'eligible'),
    possibly: items.filter((m) => m.status === 'possibly_eligible'),
    not: items.filter((m) => m.status === 'not_eligible'),
  };
}

/** Questions still to answer, most useful first (the API already orders them). */
export function nextQuestion(questions: QuestionDTO[], answered: Record<string, unknown>): QuestionDTO | null {
  return questions.find((q) => !(q.field in answered)) ?? null;
}
