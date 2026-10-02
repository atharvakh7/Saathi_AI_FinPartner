/**
 * S21 Emergency Fund: ring, saved / target, how many months of essential spending it covers,
 * suggested monthly amount and expected finish date; choose 3 / 6 / 9 / 12 months and Set up (or
 * Update) — the API creates the plan and its goal, or links an existing emergency-fund goal.
 */
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { Redirect, router } from 'expo-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { getEmergencyFund, putEmergencyFund } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import { AppText, Button, Card, Chip, ErrorBanner, MascotBubble, ProgressRing, Screen, SectionHeader, SkeletonCard } from '@/components';
import { planKeys } from '@/features/plan/plan';
import { displayDate, inr } from '@/lib/format';
import { useUiStore } from '@/stores';
import { isLoggedIn, useSessionStore } from '@/stores/session';
import { color, space } from '@/theme';

const MONTH_CHOICES = [3, 6, 9, 12];

export default function EmergencyFund() {
  const { t } = useTranslation();
  const loggedIn = useSessionStore(isLoggedIn);
  const ef = useQuery({ queryKey: planKeys.emergency, queryFn: getEmergencyFund, enabled: loggedIn });
  const [months, setMonths] = useState<number | null>(null);
  const chosen = months ?? ef.data?.target_months ?? 6;
  const save = useMutation({
    mutationFn: () => putEmergencyFund(chosen),
    onSuccess: (data) => {
      queryClient.setQueryData(planKeys.emergency, data);
      for (const key of ['plan', 'summary', 'goals', 'risk']) void queryClient.invalidateQueries({ queryKey: [key] });
      setMonths(null);
      useUiStore.getState().showToast(t('finance.form.saved'), 'success');
    },
  });
  if (!loggedIn) return <Redirect href="/onboarding/welcome" />;
  const e = ef.data;
  const preview = e ? e.monthly_essential_expense_inr * chosen : 0;
  const changed = !!e && (!e.exists || chosen !== e.target_months);

  return (
    <Screen title={t('plan.ef.title')} back
      footer={e && changed ? (
        <Button label={e.exists ? t('plan.ef.update') : t('plan.ef.setUpButton')} loading={save.isPending} onPress={() => save.mutate()} />
      ) : undefined}>
      {ef.isPending ? <SkeletonCard lines={5} /> : null}
      {ef.error ? <ErrorBanner error={ef.error} onRetry={() => void ef.refetch()} /> : null}
      {e ? (
        <>
          <MascotBubble pose="shield" size={80} text={t('plan.ef.why')} />
          <Card style={styles.hero}>
            <ProgressRing pct={e.pct} size={150} stroke={14} />
            <AppText variant="h3">{`${inr(e.current_amount_inr)} / ${inr(e.target_amount_inr)}`}</AppText>
            <AppText variant="small" muted align="center">
              {e.exists ? t('plan.ef.covers', { months: e.target_months, amount: inr(e.monthly_essential_expense_inr) })
                : t('plan.ef.notSet')}
            </AppText>
            {e.exists && e.suggested_monthly_contribution_inr > 0 ? (
              <AppText align="center">{t('plan.ef.suggest', { amount: inr(e.suggested_monthly_contribution_inr) })}</AppText>
            ) : null}
            {e.exists && e.estimated_completion_date ? (
              <AppText variant="caption" tint={color.success}>{t('plan.ef.eta', { date: displayDate(e.estimated_completion_date) })}</AppText>
            ) : null}
            {e.goal_id ? (
              <Button label={t('goals.addMoney')} variant="secondary" size="sm" fullWidth={false}
                onPress={() => router.push(`/goals/${e.goal_id}`)} />
            ) : null}
          </Card>

          <SectionHeader title={t('plan.ef.howMany')} />
          <View style={styles.chips}>
            {MONTH_CHOICES.map((m) => (
              <Chip key={m} label={t('plan.ef.months', { count: m })} selected={chosen === m} onPress={() => setMonths(m)} />
            ))}
          </View>
          <AppText variant="small" muted>{t('plan.ef.monthsHint')}</AppText>
          {e.monthly_essential_expense_inr > 0 ? (
            <Card>
              <AppText variant="small" muted>{t('plan.ef.essential', { amount: inr(e.monthly_essential_expense_inr) })}</AppText>
              <AppText variant="bodyMedium">{t('plan.ef.target', { amount: inr(preview), count: chosen })}</AppText>
            </Card>
          ) : null}
          {save.error ? (
            <ErrorBanner error={save.error} message={save.error instanceof ApiError && save.error.code === 'VALIDATION_ERROR'
              ? t('plan.ef.needData') : undefined} />
          ) : null}
        </>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: { alignItems: 'center', gap: space.sm },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
});
