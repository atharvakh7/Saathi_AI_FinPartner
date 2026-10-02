/** S26 Scheme list: by category (`?category=`), search (`?q=`) or all; filter by match status; 30 per page. */
import { useMemo, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, View } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { useInfiniteQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';

import { listSchemes, type MatchStatusDTO } from '@/api/endpoints';
import { Chip, EmptyState, ErrorBanner, Screen, SkeletonCard } from '@/components';
import { SchemeRow } from '@/features/schemes/parts';
import { schemeKeys } from '@/features/schemes/schemes';
import { useLanguageStore } from '@/stores/language';
import { color, space } from '@/theme';

type Filter = MatchStatusDTO | 'all';

export default function SchemeList() {
  const { t } = useTranslation();
  const language = useLanguageStore((s) => s.language);
  const { category, q } = useLocalSearchParams<{ category?: string; q?: string }>();
  const [status, setStatus] = useState<Filter>('all');
  const list = useInfiniteQuery({
    queryKey: schemeKeys.list(language, category ?? '', q ?? '', status),
    queryFn: ({ pageParam }) => listSchemes({ category, q, status: status === 'all' ? undefined : status, cursor: pageParam }),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => last.next_cursor,
  });
  const items = useMemo(() => list.data?.pages.flatMap((p) => p.items) ?? [], [list.data]);
  const title = category ? t(`category.${category}`) : q ? t('schemes.resultsFor', { q }) : t('schemes.all');

  return (
    <Screen title={title} back scroll={false} padded={false}>
      <FlatList
        data={items}
        keyExtractor={(s) => s.id}
        contentContainerStyle={styles.list}
        ListHeaderComponent={
          <View style={styles.header}>
            <View style={styles.chips}>
              {(['all', 'eligible', 'possibly_eligible', 'not_eligible'] as const).map((f) => (
                <Chip key={f} label={f === 'all' ? t('finance.filter.all') : t(`scheme.status.${f}`)} selected={status === f} onPress={() => setStatus(f)} />
              ))}
            </View>
            {list.isPending ? <SkeletonCard lines={3} /> : null}
            {list.error ? <ErrorBanner error={list.error} onRetry={() => void list.refetch()} /> : null}
          </View>
        }
        renderItem={({ item }) => <SchemeRow scheme={item} />}
        ListEmptyComponent={list.isSuccess ? <EmptyState pose="thinking" message={t('schemes.noResults')} /> : null}
        ListFooterComponent={list.isFetchingNextPage ? <ActivityIndicator color={color.primary} /> : null}
        onEndReached={() => { if (list.hasNextPage && !list.isFetchingNextPage) void list.fetchNextPage(); }}
        onEndReachedThreshold={0.4}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  list: { padding: space.xl, gap: space.md },
  header: { gap: space.md, marginBottom: space.xs },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
});
