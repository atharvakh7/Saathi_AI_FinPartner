/** Shared Scheme Scout pieces: category icon and a match row (scheme card + what's still needed). */
import { Briefcase, GraduationCap, HeartPulse, House, ShieldCheck, Sprout, Users, Landmark, type LucideIcon } from 'lucide-react-native';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';

import type { MatchItemDTO, SchemeSummaryDTO } from '@/api/endpoints';
import { SchemeCard } from '@/components';
import type { Tone } from '@/theme';

export const CATEGORY_ICON: Record<string, { Icon: LucideIcon; tone: Tone }> = {
  health: { Icon: HeartPulse, tone: 'neutral' },
  education: { Icon: GraduationCap, tone: 'neutral' },
  housing: { Icon: House, tone: 'neutral' },
  employment: { Icon: Briefcase, tone: 'neutral' },
  agriculture: { Icon: Sprout, tone: 'neutral' },
  women: { Icon: Users, tone: 'neutral' },
  'social-security': { Icon: ShieldCheck, tone: 'neutral' },
};
export const DEFAULT_CATEGORY = { Icon: Landmark, tone: 'neutral' as Tone };

export const openScheme = (id: string) => router.push({ pathname: '/schemes/[id]', params: { id } });

export function SchemeRow({ scheme, match }: { scheme: SchemeSummaryDTO; match?: MatchItemDTO }) {
  const { t } = useTranslation();
  const needs = match?.status === 'possibly_eligible'
    ? match.missing_fields.map((f) => t(`eligibility.field.${f}`))
    : match?.status === 'not_eligible' ? match.reasons.map((r) => r.explanation) : undefined;
  return (
    <SchemeCard name={scheme.name} benefit={scheme.benefit_summary} level={scheme.level}
      status={match?.status ?? scheme.match_status} needs={needs?.length ? needs : undefined} onPress={() => openScheme(scheme.id)} />
  );
}
