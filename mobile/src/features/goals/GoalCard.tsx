/** Goal icon + the wireframe "Top Goals" row and the S17 goal card. */
import { StyleSheet, View } from 'react-native';
import {
  Briefcase, Car, GraduationCap, HeartPulse, House, PiggyBank, ShieldCheck, Sparkles, Sprout, Target, type LucideIcon,
} from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import type { GoalDTO } from '@/api/endpoints';
import { AppText, Card, IconBadge, ProgressBar } from '@/components';
import { displayDate, inr } from '@/lib/format';
import { color, radius, space, toneColors, type Tone } from '@/theme';

const ICON: Record<string, LucideIcon> = {
  emergency_fund: ShieldCheck, education: GraduationCap, vehicle: Car, home: House, wedding: Sparkles,
  medical: HeartPulse, retirement: PiggyBank, business: Briefcase, farm_equipment: Sprout, custom: Target,
};
// Minimal style: one neutral icon colour for every goal category (colour is reserved for status).
const TONE: Record<string, Tone> = {};

export function GoalIcon({ category, size = 40 }: { category: string; size?: number }) {
  const Icon = ICON[category] ?? Target;
  const tone = TONE[category] ?? 'neutral';
  return <IconBadge tone={tone} size={size}><Icon color={toneColors[tone].fg} size={size * 0.5} /></IconBadge>;
}

/** Compact row (Home "Top Goals"): icon, title, "% complete", bar, amounts. */
export function GoalRow({ goal }: { goal: GoalDTO }) {
  const { t } = useTranslation();
  return (
    <View style={styles.row} accessible accessibilityLabel={`${goal.title}, ${goal.progress_pct}%`}>
      <GoalIcon category={goal.category} size={36} />
      <View style={styles.flex}>
        <View style={styles.between}>
          <AppText variant="small" style={styles.flex} numberOfLines={1}>{goal.title}</AppText>
          <AppText variant="caption" muted>{`${inr(goal.current_amount_inr)} / ${inr(goal.target_amount_inr)}`}</AppText>
        </View>
        <ProgressBar pct={goal.progress_pct} />
        <AppText variant="caption" tint={color.success}>{t('goals.pctComplete', { pct: goal.progress_pct })}</AppText>
      </View>
    </View>
  );
}

/** S17 card: icon, title, status chip, bar, amounts, target date. */
export function GoalCard({ goal, onPress }: { goal: GoalDTO; onPress: () => void }) {
  const { t } = useTranslation();
  const chip = goal.status === 'paused' ? { tone: 'warning' as Tone, label: t('goals.status.paused') }
    : goal.status === 'completed' ? { tone: 'positive' as Tone, label: t('goals.status.completed') }
    : goal.projection.on_track === true ? { tone: 'positive' as Tone, label: t('goals.onTrack') }
    : goal.projection.on_track === false ? { tone: 'warning' as Tone, label: t('goals.behind') }
    : null;
  return (
    <Card onPress={onPress} accessibilityLabel={`${goal.title}, ${goal.progress_pct}%`}>
      <View style={styles.row}>
        <GoalIcon category={goal.category} />
        <View style={styles.flex}>
          <AppText variant="bodyMedium" numberOfLines={1}>{goal.title}</AppText>
          <AppText variant="caption" muted>
            {goal.target_date ? t('goals.byDate', { date: displayDate(goal.target_date) }) : t('onboarding.goals.noDate')}
          </AppText>
        </View>
        {chip ? (
          <View style={[styles.chip, { backgroundColor: toneColors[chip.tone].bg }]}>
            <AppText variant="caption" tint={toneColors[chip.tone].fg}>{chip.label}</AppText>
          </View>
        ) : null}
      </View>
      <ProgressBar pct={goal.progress_pct} height={8} tint={goal.status === 'paused' ? color.warning : color.success} />
      <View style={styles.between}>
        <AppText variant="small"><AppText variant="bodyMedium">{inr(goal.current_amount_inr)}</AppText>{` / ${inr(goal.target_amount_inr)}`}</AppText>
        <AppText variant="small" tint={color.success}>{t('goals.pctComplete', { pct: goal.progress_pct })}</AppText>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  row: { flexDirection: 'row', alignItems: 'center', gap: space.md },
  between: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: space.sm },
  chip: { paddingHorizontal: space.sm, paddingVertical: 2, borderRadius: radius.pill },
});
