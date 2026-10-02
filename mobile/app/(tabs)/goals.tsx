/** S17 Goals (tab): Active (active + paused) | Completed, a total-saved summary, goal cards, New goal. */
import { useState } from 'react';
import { RefreshControl, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Plus } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { listGoals } from '@/api/endpoints';
import { AppText, Button, Card, EmptyState, ErrorBanner, PageHeader, ProgressBar, Screen, SegmentedTabs, SkeletonCard } from '@/components';
import { GoalCard } from '@/features/goals/GoalCard';
import { goalKeys } from '@/features/goals/goals';
import { inr } from '@/lib/format';
import { color, space } from '@/theme';

type Tab = 'active' | 'completed';

export default function Goals() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>('active');
  const goals = useQuery({ queryKey: goalKeys.list(tab), queryFn: () => listGoals(tab) });
  const list = goals.data ?? [];
  const saved = list.reduce((s, g) => s + g.current_amount_inr, 0);
  const target = list.reduce((s, g) => s + g.target_amount_inr, 0);
  const add = () => router.push('/goals/new');

  return (
    <Screen
      refreshControl={<RefreshControl refreshing={goals.isRefetching} onRefresh={() => void goals.refetch()} />}
      footer={<Button label={t('goals.new')} icon={<Plus color={color.onPrimary} size={20} />} onPress={add} />}>
      <PageHeader title={t('goals.title')} subtitle={t('goals.subtitle')} pose="thumbs_up" />
      <SegmentedTabs<Tab> value={tab} onChange={setTab} options={[
        { value: 'active', label: t('goals.tab.active') },
        { value: 'completed', label: t('goals.tab.completed') },
      ]} />
      {goals.isPending ? <><SkeletonCard /><SkeletonCard /></> : null}
      {goals.error ? <ErrorBanner error={goals.error} onRetry={() => void goals.refetch()} /> : null}
      {tab === 'active' && list.length > 1 ? (
        <Card>
          <View style={styles.between}>
            <AppText variant="small" muted>{t('goals.totalSaved')}</AppText>
            <AppText variant="small" muted>{t('goals.pctComplete', { pct: target ? Math.min(100, Math.floor((100 * saved) / target)) : 0 })}</AppText>
          </View>
          <AppText variant="h2">{inr(saved)}<AppText muted>{` / ${inr(target)}`}</AppText></AppText>
          <ProgressBar pct={target ? (100 * saved) / target : 0} height={8} />
        </Card>
      ) : null}
      {goals.data && list.length === 0 ? (
        tab === 'active'
          ? <EmptyState pose="point_up" message={t('goals.empty')} actionLabel={t('goals.new')} onAction={add} />
          : <EmptyState pose="thinking" message={t('goals.emptyCompleted')} />
      ) : null}
      {list.map((g) => <GoalCard key={g.id} goal={g} onPress={() => router.push(`/goals/${g.id}`)} />)}
    </Screen>
  );
}

const styles = StyleSheet.create({
  between: { flexDirection: 'row', justifyContent: 'space-between', gap: space.sm },
});
