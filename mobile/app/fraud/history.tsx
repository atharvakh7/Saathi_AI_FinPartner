/** S31 Check history: past checks newest first (kept 180 days), 30 per page; tap for the result. */
import { useMemo } from 'react';
import { ActivityIndicator, FlatList, StyleSheet } from 'react-native';
import { router } from 'expo-router';
import { useInfiniteQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';

import { listFraudChecks } from '@/api/endpoints';
import { AppText, EmptyState, ErrorBanner, Screen, SkeletonCard } from '@/components';
import { FraudRow } from '@/features/fraud/parts';
import { fraudKeys } from '@/features/fraud/fraud';
import { color, space } from '@/theme';

export default function FraudHistory() {
  const { t } = useTranslation();
  const list = useInfiniteQuery({
    queryKey: [...fraudKeys.checks, 'all'],
    queryFn: ({ pageParam }) => listFraudChecks(pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => last.next_cursor,
  });
  const items = useMemo(() => list.data?.pages.flatMap((p) => p.items) ?? [], [list.data]);
  return (
    <Screen title={t('fraud.history')} back scroll={false} padded={false}>
      <FlatList
        data={items}
        keyExtractor={(c) => c.id}
        contentContainerStyle={styles.list}
        ListHeaderComponent={<>
          {list.isPending ? <SkeletonCard lines={4} /> : null}
          {list.error ? <ErrorBanner error={list.error} onRetry={() => void list.refetch()} /> : null}
          {items.length ? <AppText variant="caption" muted>{t('fraud.kept')}</AppText> : null}
        </>}
        renderItem={({ item }) => <FraudRow check={item} />}
        ListEmptyComponent={list.isSuccess ? <EmptyState pose="shield" message={t('fraud.historyEmpty')} actionLabel={t('fraud.check')} onAction={() => router.replace('/fraud' as never)} /> : null}
        ListFooterComponent={list.isFetchingNextPage ? <ActivityIndicator color={color.primary} /> : null}
        onEndReached={() => { if (list.hasNextPage && !list.isFetchingNextPage) void list.fetchNextPage(); }}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({ list: { padding: space.xl, gap: space.md } });
