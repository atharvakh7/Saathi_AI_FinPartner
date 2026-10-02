/**
 * S14 Transactions: month switcher (current month by default), All / Income / Expenses, the month's
 * totals, entries grouped by day (newest first, 30 per page, more on scroll). Tap to edit.
 */
import { useMemo, useState } from 'react';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { Plus } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { getSummary, listTransactions, type TransactionDTO } from '@/api/endpoints';
import { AppText, Button, Card, EmptyState, ErrorBanner, Screen, SegmentedTabs, SkeletonCard } from '@/components';
import { groupByDay } from '@/features/finance/list';
import { financeKeys, rememberTransaction } from '@/features/finance/queries';
import { MonthSwitcher, TransactionRow } from '@/features/finance/parts';
import { apiMonth, dayLabel, inr } from '@/lib/format';
import type { TxType } from '@/lib/constants';
import { color, space } from '@/theme';

type Filter = TxType | 'all';

export default function Transactions() {
  const { t } = useTranslation();
  const params = useLocalSearchParams<{ type?: string; month?: string }>();
  const [month, setMonth] = useState(params.month && /^\d{4}-\d{2}$/.test(params.month) ? params.month : apiMonth());
  const [filter, setFilter] = useState<Filter>(params.type === 'income' || params.type === 'expense' ? params.type : 'all');

  const totals = useQuery({ queryKey: financeKeys.summary(month), queryFn: () => getSummary(month) });
  const list = useInfiniteQuery({
    queryKey: financeKeys.transactions(month, filter),
    queryFn: ({ pageParam }) => listTransactions({ month, type: filter === 'all' ? undefined : filter, cursor: pageParam }),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => last.next_cursor,
  });
  const items = useMemo(() => groupByDay(list.data?.pages.flatMap((p) => p.items) ?? []), [list.data]);

  const open = (tx: TransactionDTO) => {
    rememberTransaction(tx);
    router.push({ pathname: '/finance/transaction', params: { id: tx.id } });
  };
  const add = () => router.push({ pathname: '/finance/transaction', params: { type: filter === 'income' ? 'income' : 'expense' } });

  const header = (
    <View style={styles.header}>
      <MonthSwitcher month={month} onChange={setMonth} />
      <SegmentedTabs<Filter> value={filter} onChange={setFilter} options={[
        { value: 'all', label: t('finance.filter.all') },
        { value: 'income', label: t('finance.filter.income') },
        { value: 'expense', label: t('finance.filter.expense') },
      ]} />
      {totals.data ? (
        <Card style={styles.totals}>
          <View style={styles.total}>
            <AppText variant="small" muted>{t('home.income')}</AppText>
            <AppText variant="bodyMedium" tint={color.success}>{inr(totals.data.income_inr)}</AppText>
          </View>
          <View style={styles.total}>
            <AppText variant="small" muted>{t('home.expenses')}</AppText>
            <AppText variant="bodyMedium">{inr(totals.data.expenses_inr)}</AppText>
          </View>
          <View style={styles.total}>
            <AppText variant="small" muted>{t('home.savings')}</AppText>
            <AppText variant="bodyMedium" tint={totals.data.savings_inr < 0 ? color.danger : color.primary}>
              {inr(totals.data.savings_inr)}
            </AppText>
          </View>
        </Card>
      ) : null}
      {list.isPending ? <SkeletonCard lines={5} /> : null}
      {list.error ? <ErrorBanner error={list.error} onRetry={() => void list.refetch()} /> : null}
    </View>
  );

  return (
    <Screen title={t('finance.transactions.title')} back scroll={false} padded={false}
      footer={<Button label={t('finance.transactions.add')} icon={<Plus color={color.onPrimary} size={20} />} onPress={add} />}>
      <FlatList
        data={items}
        keyExtractor={(it) => (it.kind === 'day' ? `d-${it.date}` : it.tx.id)}
        contentContainerStyle={styles.list}
        ListHeaderComponent={header}
        renderItem={({ item }) => {
          if (item.kind === 'day') {
            const label = dayLabel(item.date);
            return <AppText variant="small" muted style={styles.day} accessibilityRole="header">{label.key ? t(label.key) : label.text}</AppText>;
          }
          return <TransactionRow tx={item.tx} onPress={() => open(item.tx)} />;
        }}
        ListEmptyComponent={list.isSuccess ? (
          <EmptyState pose="point_up" message={t('finance.transactions.empty')} actionLabel={t('finance.transactions.add')} onAction={add} />
        ) : null}
        ListFooterComponent={list.isFetchingNextPage ? <ActivityIndicator color={color.primary} style={styles.more} /> : null}
        onEndReached={() => { if (list.hasNextPage && !list.isFetchingNextPage) void list.fetchNextPage(); }}
        onEndReachedThreshold={0.4}
        refreshControl={<RefreshControl refreshing={list.isRefetching && !list.isFetchingNextPage}
          onRefresh={() => { void list.refetch(); void totals.refetch(); }} />}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  list: { paddingHorizontal: space.xl, paddingBottom: space.xl },
  header: { gap: space.md, paddingTop: space.sm, paddingBottom: space.sm },
  totals: { flexDirection: 'row', gap: space.sm },
  total: { flex: 1, gap: 2 },
  day: { marginTop: space.lg, marginBottom: space.sm, marginLeft: space.xs },
  more: { marginVertical: space.lg },
});
