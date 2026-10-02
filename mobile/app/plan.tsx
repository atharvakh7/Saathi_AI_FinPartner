/**
 * S20 Plan — reached from Services (wireframe "Irregular Income Planner"): income pattern, monthly snapshot (income bars,
 * lean months highlighted), tight-month warning, cash-flow outlook (next 6 months), this month's
 * budget (needs / wants / savings, Recalculate), recommended savings, emergency fund and risk cards.
 * No data -> "Tell me about your income" (S20 empty state).
 */
import { RefreshControl, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { CircleAlert, PiggyBank, RefreshCw } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { getOverview, getRisk, regenerateBudget, type BudgetDTO, type BudgetMode } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import {
  AppText, Button, Card, EmptyState, ErrorBanner, IconBadge, PageHeader, ProgressBar, ProgressRing, RiskGauge, Screen,
  SectionHeader, SkeletonCard,
} from '@/components';
import { IncomeBars, OutlookChart } from '@/features/plan/charts';
import { planKeys } from '@/features/plan/plan';
import { displayMonth, inr } from '@/lib/format';
import { useUiStore } from '@/stores';
import { color, radius, space, toneColors, type Tone } from '@/theme';

const MODE_TONE: Record<BudgetMode, Tone> = { lean: 'warning', normal: 'neutral', surplus: 'positive' };

export default function Plan() {
  const { t } = useTranslation();
  const overview = useQuery({ queryKey: planKeys.overview, queryFn: getOverview });
  const risk = useQuery({ queryKey: planKeys.risk, queryFn: getRisk, retry: false });
  const recalc = useMutation({
    mutationFn: regenerateBudget,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['plan'] });
      useUiStore.getState().showToast(t('plan.recalculated'), 'success');
    },
    onError: () => useUiStore.getState().showToast(t('errors.RATE_LIMITED'), 'error'),
  });
  const o = overview.data;
  const refresh = () => { void overview.refetch(); void risk.refetch(); };

  return (
    <Screen back refreshControl={<RefreshControl refreshing={overview.isRefetching} onRefresh={refresh} />}>
      <PageHeader title={t('plan.title')} subtitle={t('plan.subtitle')} pose="point_up" />
      {overview.isPending ? <><SkeletonCard lines={4} /><SkeletonCard lines={4} /></> : null}
      {overview.error ? <ErrorBanner error={overview.error} onRetry={refresh} /> : null}

      {o && !o.has_data ? (
        <EmptyState pose="point_up" message={t('plan.empty')} actionLabel={t('home.addIncome')}
          onAction={() => router.push({ pathname: '/finance/transaction', params: { type: 'income' } })} />
      ) : null}

      {o && o.has_data ? (
        <>
          <View style={styles.chips}>
            <Pill tone="neutral" label={t(`plan.pattern.${o.pattern.label}`)} />
            <Pill tone="neutral" label={t(`plan.confidence.${o.data_confidence}`)} />
          </View>

          {o.income_history.length ? (
            <Card>
              <SectionHeader title={t('plan.snapshot')} />
              <IncomeBars data={o.income_history.slice(-6)} />
              {o.income_history.some((m) => m.is_lean) ? <AppText variant="caption" muted>{t('plan.leanHint')}</AppText> : null}
            </Card>
          ) : null}

          {o.tight_months.length ? (
            <View style={[styles.alert, { backgroundColor: toneColors.warning.bg }]} accessibilityRole="alert">
              <CircleAlert color={toneColors.warning.fg} size={20} />
              <AppText variant="small" tint={toneColors.warning.fg} style={styles.flex}>
                {t('plan.tightMonths', { months: o.tight_months.map(displayMonth).join(', ') })}
              </AppText>
            </View>
          ) : null}

          {o.forecast.length ? (
            <Card>
              <SectionHeader title={t('plan.outlook')} />
              <AppText variant="caption" muted>{t('plan.outlookHint', { count: o.forecast.length })}</AppText>
              <OutlookChart data={o.forecast} />
            </Card>
          ) : null}

          <BudgetCard budget={o.current_budget} onRecalc={() => recalc.mutate()} recalculating={recalc.isPending} />

          {o.current_budget.savings_target_inr > 0 ? (
            <Card style={styles.row}>
              <IconBadge tone="accent" size={48}><PiggyBank color={color.accent} size={26} /></IconBadge>
              <View style={styles.flex}>
                <AppText variant="bodyMedium">{t('plan.recommended')}</AppText>
                <AppText>{t('plan.saveThisMonth', { amount: inr(o.current_budget.savings_target_inr) })}</AppText>
                {o.current_budget.planning_income_inr > 0 ? (
                  <AppText variant="caption" muted>{t('plan.pctOfIncome', {
                    pct: Math.round((100 * o.current_budget.savings_target_inr) / o.current_budget.planning_income_inr),
                  })}</AppText>
                ) : null}
              </View>
            </Card>
          ) : null}
        </>
      ) : null}

      {o ? (
        <View style={styles.tiles}>
          <Card style={styles.tile} onPress={() => router.push('/emergency-fund')} accessibilityLabel={t('plan.ef.title')}>
            <AppText variant="small" muted>{t('plan.ef.title')}</AppText>
            <View style={styles.center}>
              <ProgressRing pct={o.emergency_fund.pct} size={84} stroke={9} />
            </View>
            <AppText variant="caption" muted align="center" numberOfLines={2}>
              {o.emergency_fund.exists ? `${inr(o.emergency_fund.current_inr)} / ${inr(o.emergency_fund.target_inr)}` : t('plan.ef.setUp')}
            </AppText>
          </Card>
          <Card style={styles.tile} onPress={() => router.push('/risk')} accessibilityLabel={t('risk.title')}>
            <AppText variant="small" muted>{t('risk.title')}</AppText>
            {risk.data ? (
              <View style={styles.center}><RiskGauge score={risk.data.score} level={risk.data.level} size={120} /></View>
            ) : (
              <AppText variant="caption" muted align="center">{t('plan.riskEmpty')}</AppText>
            )}
            <AppText variant="caption" tint={color.primaryLight} align="center">{t('plan.seeReport')}</AppText>
          </Card>
        </View>
      ) : null}
    </Screen>
  );
}

function BudgetCard({ budget: b, onRecalc, recalculating }: { budget: BudgetDTO; onRecalc: () => void; recalculating: boolean }) {
  const { t } = useTranslation();
  const rows = [
    { key: 'needs', spent: b.spent_needs_inr, limit: b.needs_limit_inr, tint: color.primaryLight },
    { key: 'wants', spent: b.spent_wants_inr, limit: b.wants_limit_inr, tint: color.accent },
  ] as const;
  return (
    <Card>
      <View style={styles.row}>
        <AppText variant="bodyMedium" style={styles.flex}>{t('plan.budget', { month: displayMonth(b.month) })}</AppText>
        <Pill tone={MODE_TONE[b.mode]} label={t(`plan.mode.${b.mode}`)} />
      </View>
      <AppText variant="caption" muted>{t('plan.planningIncome', { amount: inr(b.planning_income_inr) })}</AppText>
      {rows.map((r) => {
        const over = r.limit > 0 && r.spent > r.limit;
        return (
          <View key={r.key} style={styles.budgetRow}>
            <View style={styles.row}>
              <AppText variant="small" style={styles.flex}>{t(`plan.${r.key}`)}</AppText>
              <AppText variant="small" tint={over ? color.danger : color.text}>{`${inr(r.spent)} / ${inr(r.limit)}`}</AppText>
            </View>
            <ProgressBar pct={r.limit > 0 ? (100 * r.spent) / r.limit : 0} tint={over ? color.danger : r.tint} height={8} />
            {over ? <AppText variant="caption" tint={color.danger}>{t('plan.over', { amount: inr(r.spent - r.limit) })}</AppText> : null}
          </View>
        );
      })}
      <View style={styles.budgetRow}>
        <View style={styles.row}>
          <AppText variant="small" style={styles.flex}>{t('plan.savings')}</AppText>
          <AppText variant="small" tint={color.success}>{`${inr(Math.max(0, b.saved_so_far_inr))} / ${inr(b.savings_target_inr)}`}</AppText>
        </View>
        <ProgressBar pct={b.savings_target_inr > 0 ? (100 * Math.max(0, b.saved_so_far_inr)) / b.savings_target_inr : 0} height={8} />
      </View>
      <Button label={t('plan.recalculate')} variant="ghost" size="sm" loading={recalculating}
        icon={<RefreshCw color={color.primary} size={16} />} onPress={onRecalc} />
    </Card>
  );
}

function Pill({ tone, label }: { tone: Tone; label: string }) {
  return (
    <View style={[styles.pill, { backgroundColor: toneColors[tone].bg }]}>
      <AppText variant="caption" tint={toneColors[tone].fg}>{label}</AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  row: { flexDirection: 'row', alignItems: 'center', gap: space.md },
  center: { alignItems: 'center', paddingVertical: space.xs },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
  pill: { paddingHorizontal: space.md, paddingVertical: space.xs, borderRadius: radius.pill },
  alert: { flexDirection: 'row', alignItems: 'center', gap: space.sm, padding: space.md, borderRadius: radius.md },
  budgetRow: { gap: space.xs, marginTop: space.xs },
  tiles: { flexDirection: 'row', gap: space.md },
  tile: { flex: 1, minWidth: 0 },
});
