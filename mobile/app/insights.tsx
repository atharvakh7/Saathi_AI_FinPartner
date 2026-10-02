/**
 * S11 Insights: Saathi's tips about your money (newest first, last 30 days), filtered All / Savings /
 * Spending / Goals; unread ones marked. Tapping marks it read and opens the related screen.
 */
import { useMemo, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, View } from 'react-native';
import { Redirect } from 'expo-router';
import { useInfiniteQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';

import { listInsights, type InsightFilter } from '@/api/endpoints';
import { EmptyState, ErrorBanner, InsightCard, Screen, SegmentedTabs, SkeletonCard } from '@/components';
import { insightKeys, insightText } from '@/features/insights/insights';
import { openInsight } from '@/features/insights/open';
import { appRoute } from '@/lib/routes';
import { useLanguageStore } from '@/stores/language';
import { isLoggedIn, useSessionStore } from '@/stores/session';
import { color, space } from '@/theme';

export default function Insights() {
  const { t, i18n } = useTranslation();
  const loggedIn = useSessionStore(isLoggedIn);
  const language = useLanguageStore((s) => s.language);
  const [filter, setFilter] = useState<InsightFilter>('all');
  const list = useInfiniteQuery({
    queryKey: insightKeys.list(filter, language),
    queryFn: ({ pageParam }) => listInsights(filter, pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => last.next_cursor,
    enabled: loggedIn,
  });
  const items = useMemo(() => list.data?.pages.flatMap((p) => p.items) ?? [], [list.data]);
  if (!loggedIn) return <Redirect href="/onboarding/welcome" />;

  return (
    <Screen title={t('insights.title')} back scroll={false} padded={false}>
      <FlatList
        data={items}
        keyExtractor={(i) => i.id}
        contentContainerStyle={styles.list}
        ListHeaderComponent={
          <View style={styles.header}>
            <SegmentedTabs<InsightFilter> value={filter} onChange={setFilter} options={[
              { value: 'all', label: t('finance.filter.all') }, { value: 'savings', label: t('insights.savings') },
              { value: 'spending', label: t('insights.spending') }, { value: 'goals', label: t('home.goals') },
            ]} />
            {list.isPending ? <><SkeletonCard lines={2} /><SkeletonCard lines={2} /></> : null}
            {list.error ? <ErrorBanner error={list.error} onRetry={() => void list.refetch()} /> : null}
          </View>
        }
        renderItem={({ item }) => {
          const text = insightText(item, language, t, (k) => i18n.exists(k));
          return (
            <InsightCard tone={item.tone} title={text.title} body={text.body} unread={!item.is_read}
              ctaLabel={appRoute(item.cta_route) ? t('insights.open') : undefined} onPress={() => openInsight(item)} />
          );
        }}
        ListEmptyComponent={list.isSuccess ? <EmptyState pose="thinking" message={t('insights.empty')} /> : null}
        ListFooterComponent={list.isFetchingNextPage ? <ActivityIndicator color={color.primary} /> : null}
        onEndReached={() => { if (list.hasNextPage && !list.isFetchingNextPage) void list.fetchNextPage(); }}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  list: { padding: space.xl, gap: space.md },
  header: { gap: space.md, marginBottom: space.xs },
});
