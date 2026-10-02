/**
 * S12 Risk Report: 0–5 gauge with level (icon + text), date, what adds to the score (the four parts,
 * biggest first, each with a bar and a localized tip), and the last 90 days of scores.
 * No data -> "Add income and expenses to see your score." (API 404).
 */
import { RefreshControl, StyleSheet, View } from 'react-native';
import { Redirect, router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import Svg, { Path } from 'react-native-svg';
import { useState } from 'react';

import { ApiError } from '@/api/client';
import { getRisk, getRiskHistory } from '@/api/endpoints';
import { AppText, Card, EmptyState, ErrorBanner, ProgressBar, RiskGauge, Screen, SectionHeader, SkeletonCard } from '@/components';
import { partLevel, planKeys, riskContributions } from '@/features/plan/plan';
import { displayDate } from '@/lib/format';
import { isLoggedIn, useSessionStore } from '@/stores/session';
import { color, space, toneColors } from '@/theme';

const LEVEL_TINT = { low: color.success, medium: color.warning, high: color.danger } as const;

export default function RiskReport() {
  const { t } = useTranslation();
  const loggedIn = useSessionStore(isLoggedIn);
  const risk = useQuery({ queryKey: planKeys.risk, queryFn: getRisk, retry: false, enabled: loggedIn });
  const history = useQuery({ queryKey: planKeys.riskHistory, queryFn: () => getRiskHistory(90), enabled: loggedIn && !!risk.data });
  if (!loggedIn) return <Redirect href="/onboarding/welcome" />;
  const noData = risk.error instanceof ApiError && risk.error.code === 'NOT_FOUND';
  const r = risk.data;

  return (
    <Screen title={t('risk.report')} back
      refreshControl={<RefreshControl refreshing={risk.isRefetching} onRefresh={() => { void risk.refetch(); void history.refetch(); }} />}>
      {risk.isPending ? <SkeletonCard lines={5} /> : null}
      {noData ? (
        <EmptyState pose="thinking" message={t('risk.empty')} actionLabel={t('home.addIncome')}
          onAction={() => router.push({ pathname: '/finance/transaction', params: { type: 'income' } })} />
      ) : risk.error ? <ErrorBanner error={risk.error} onRetry={() => void risk.refetch()} /> : null}

      {r ? (
        <>
          <Card style={styles.hero}>
            <RiskGauge score={r.score} level={r.level} />
            <AppText align="center">{t(`risk.summary.${r.level}`)}</AppText>
            <AppText variant="caption" muted>{t('risk.updated', { date: displayDate(r.computed_on) })}</AppText>
          </Card>

          <SectionHeader title={t('risk.whatAdds')} />
          <AppText variant="caption" muted>{t('risk.whatAddsHint')}</AppText>
          {riskContributions(r.components).map((c) => {
            const lvl = partLevel(c.value);
            return (
              <Card key={c.key}>
                <View style={styles.row}>
                  <AppText variant="bodyMedium" style={styles.flex}>{t(`risk.component.${c.key}`)}</AppText>
                  <AppText variant="small" tint={LEVEL_TINT[lvl]}>{t('risk.points', { points: c.points.toFixed(1) })}</AppText>
                </View>
                <ProgressBar pct={c.value * 100} tint={LEVEL_TINT[lvl]} height={8} />
                <View style={[styles.tip, { backgroundColor: toneColors.neutral.bg }]}>
                  <AppText variant="small" tint={color.primary}>{t(`risk.tip.${c.key}`)}</AppText>
                </View>
              </Card>
            );
          })}

          {history.data && history.data.length > 1 ? (
            <Card>
              <SectionHeader title={t('risk.history')} />
              <ScoreLine scores={history.data.map((h) => h.score)} />
              <View style={styles.row}>
                <AppText variant="caption" muted style={styles.flex}>{displayDate(history.data[0]!.computed_on)}</AppText>
                <AppText variant="caption" muted>{displayDate(history.data[history.data.length - 1]!.computed_on)}</AppText>
              </View>
            </Card>
          ) : null}
        </>
      ) : null}
    </Screen>
  );
}

/** Score over time, 0 (bottom) to 5 (top); lower is better. */
function ScoreLine({ scores }: { scores: number[] }) {
  const { t } = useTranslation();
  const [w, setW] = useState(0);
  const h = 80;
  const d = scores.map((s, i) => `${i ? 'L' : 'M'}${(i * w) / (scores.length - 1)},${h - 4 - (s / 5) * (h - 8)}`).join(' ');
  return (
    <View onLayout={(e) => setW(e.nativeEvent.layout.width)} accessible
      accessibilityLabel={t('risk.historyA11y', { from: scores[0]!.toFixed(1), to: scores[scores.length - 1]!.toFixed(1) })}>
      {w ? <Svg width={w} height={h}><Path d={d} stroke={color.primaryLight} strokeWidth={2.5} fill="none" strokeLinejoin="round" /></Svg> : <View style={{ height: h }} />}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  hero: { alignItems: 'center', gap: space.sm },
  row: { flexDirection: 'row', alignItems: 'center', gap: space.sm },
  tip: { padding: space.md, borderRadius: 12 },
});
