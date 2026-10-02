/**
 * S16 Debts: total still to pay across active debts, each debt as a card (lender, type, amount left,
 * interest, monthly payment, due day), paid-off debts below. Tap a card to edit.
 */
import { RefreshControl, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Plus } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { listDebts, type DebtDTO } from '@/api/endpoints';
import { AppText, Button, Card, EmptyState, ErrorBanner, MascotBubble, Screen, SkeletonCard } from '@/components';
import { DEBT_ICON } from '@/features/finance/categories';
import { financeKeys } from '@/features/finance/queries';
import { inr } from '@/lib/format';
import { color, space, toneColors } from '@/theme';

function DebtCard({ debt }: { debt: DebtDTO }) {
  const { t } = useTranslation();
  const Icon = DEBT_ICON[debt.debt_type];
  const closed = debt.status === 'closed';
  const details = [
    debt.interest_rate_pct > 0 ? t('finance.debt.ratePerYear', { rate: String(Number(debt.interest_rate_pct.toFixed(2))) }) : null,
    debt.min_monthly_payment_inr > 0 ? t('finance.debt.perMonth', { amount: inr(debt.min_monthly_payment_inr) }) : null,
    debt.due_day_of_month ? t('finance.debt.dueOn', { day: debt.due_day_of_month }) : null,
  ].filter(Boolean).join(' · ');
  return (
    <Card onPress={() => router.push({ pathname: '/finance/debt', params: { id: debt.id } })}
      accessibilityLabel={`${debt.lender_name}, ${inr(debt.principal_outstanding_inr)}`} style={closed ? styles.closed : undefined}>
      <View style={styles.row}>
        <View style={[styles.icon, { backgroundColor: closed ? color.bg : toneColors.neutral.bg }]}>
          <Icon color={closed ? color.textMuted : toneColors.neutral.fg} size={20} />
        </View>
        <View style={styles.flex}>
          <AppText variant="bodyMedium" numberOfLines={1}>{debt.lender_name}</AppText>
          <AppText variant="small" muted>{t(`debttype.${debt.debt_type}`)}</AppText>
        </View>
        <View style={styles.amount}>
          <AppText variant="bodyMedium">{inr(debt.principal_outstanding_inr)}</AppText>
          <AppText variant="caption" muted>{closed ? t('finance.debt.paidOff') : t('finance.debt.left')}</AppText>
        </View>
      </View>
      {details ? <AppText variant="small" muted>{details}</AppText> : null}
    </Card>
  );
}

export default function Debts() {
  const { t } = useTranslation();
  const debts = useQuery({ queryKey: financeKeys.debts, queryFn: listDebts });
  const all = debts.data ?? [];
  const active = all.filter((d) => d.status === 'active');
  const closed = all.filter((d) => d.status === 'closed');
  const total = active.reduce((sum, d) => sum + d.principal_outstanding_inr, 0);
  const add = () => router.push('/finance/debt');

  return (
    <Screen title={t('finance.debt.title')} back
      refreshControl={<RefreshControl refreshing={debts.isRefetching} onRefresh={() => void debts.refetch()} />}
      footer={<Button label={t('finance.debt.add')} icon={<Plus color={color.onPrimary} size={20} />} onPress={add} />}>
      {debts.isPending ? <SkeletonCard lines={4} /> : null}
      {debts.error ? <ErrorBanner error={debts.error} onRetry={() => void debts.refetch()} /> : null}
      {debts.data && all.length === 0 ? (
        <EmptyState pose="thumbs_up" message={t('finance.debt.empty')} actionLabel={t('finance.debt.add')} onAction={add} />
      ) : null}
      {active.length ? (
        <Card style={styles.total}>
          <AppText variant="small" muted>{t('finance.debt.total')}</AppText>
          <AppText variant="h1">{inr(total)}</AppText>
          <AppText variant="small" muted>{t('home.debtActive', { count: active.length })}</AppText>
        </Card>
      ) : null}
      {debts.data && all.length > 0 && active.length === 0 ? (
        <MascotBubble pose="thumbs_up" text={t('finance.debt.allPaid')} size={80} />
      ) : null}
      {active.map((d) => <DebtCard key={d.id} debt={d} />)}
      {closed.length ? <AppText variant="h3" style={styles.section}>{t('finance.debt.paidOffSection')}</AppText> : null}
      {closed.map((d) => <DebtCard key={d.id} debt={d} />)}
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  row: { flexDirection: 'row', alignItems: 'center', gap: space.md },
  icon: { width: 40, height: 40, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  amount: { alignItems: 'flex-end' },
  total: { alignItems: 'center', gap: space.xs },
  closed: { opacity: 0.7 },
  section: { marginTop: space.sm },
});
