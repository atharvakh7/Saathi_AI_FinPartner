/** Planner query keys and small pure helpers for S12 / S20 / S21. */
import type { RiskDTO } from '@/api/endpoints';

export const planKeys = {
  overview: ['plan', 'overview'] as const,
  risk: ['risk', 'current'] as const,
  riskHistory: ['risk', 'history'] as const,
  emergency: ['emergency'] as const,
};

/** How much each part adds to the 0–5 score (value × weight × 5), biggest first. */
export function riskContributions(components: RiskDTO['components']): { key: RiskDTO['components'][number]['key']; points: number; value: number }[] {
  return components
    .map((c) => ({ key: c.key, value: c.value, points: Math.round(c.value * c.weight * 5 * 10) / 10 }))
    .sort((a, b) => b.points - a.points);
}

/** Bar colour for one risk part: 0–0.33 good, to 0.66 watch, above needs work. */
export function partLevel(value: number): 'low' | 'medium' | 'high' {
  if (value <= 0.33) return 'low';
  if (value <= 0.66) return 'medium';
  return 'high';
}
