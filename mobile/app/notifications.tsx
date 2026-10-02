/**
 * S13 Notifications: everything Saathi sent or would have sent (in-app inbox, also when push is off),
 * newest first, unread dot; tap -> mark read and open its screen; Mark all read.
 */
import { useMemo } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, View } from 'react-native';
import { Redirect, router } from 'expo-router';
import { useInfiniteQuery, useMutation } from '@tanstack/react-query';
import { Bell, CheckCheck } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { listNotifications, markAllNotificationsRead, markNotificationRead, type NotificationDTO } from '@/api/endpoints';
import { AppText, Button, EmptyState, ErrorBanner, IconBadge, Screen, SkeletonCard } from '@/components';
import { insightKeys, invalidateInbox } from '@/features/insights/insights';
import { relativeTime } from '@/lib/format';
import { appRoute } from '@/lib/routes';
import { isLoggedIn, useSessionStore } from '@/stores/session';
import { color, radius, shadow, space } from '@/theme';

export default function Notifications() {
  const { t } = useTranslation();
  const loggedIn = useSessionStore(isLoggedIn);
  const list = useInfiniteQuery({
    queryKey: insightKeys.notifications,
    queryFn: ({ pageParam }) => listNotifications(pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => last.next_cursor,
    enabled: loggedIn,
  });
  const items = useMemo(() => list.data?.pages.flatMap((p) => p.items) ?? [], [list.data]);
  const readAll = useMutation({ mutationFn: markAllNotificationsRead, onSuccess: invalidateInbox });
  if (!loggedIn) return <Redirect href="/onboarding/welcome" />;

  const open = (n: NotificationDTO) => {
    if (!n.read) void markNotificationRead(n.id).then(invalidateInbox).catch(() => undefined);
    const route = appRoute(n.data?.route);
    if (route) router.push(route as never);
  };

  return (
    <Screen title={t('notifications.title')} back scroll={false} padded={false}
      right={items.some((n) => !n.read) ? (
        <Button label={t('notifications.readAll')} variant="ghost" size="sm" fullWidth={false} loading={readAll.isPending}
          icon={<CheckCheck color={color.primary} size={16} />} onPress={() => readAll.mutate()} />
      ) : undefined}>
      <FlatList
        data={items}
        keyExtractor={(n) => n.id}
        contentContainerStyle={styles.list}
        ListHeaderComponent={<>
          {list.isPending ? <SkeletonCard lines={3} /> : null}
          {list.error ? <ErrorBanner error={list.error} onRetry={() => void list.refetch()} /> : null}
        </>}
        renderItem={({ item }) => {
          const [key, count] = relativeTime(item.created_at);
          return (
            <Pressable onPress={() => open(item)} accessibilityRole="button" accessibilityLabel={`${item.title}. ${item.body}`}
              style={({ pressed }) => [styles.row, !item.read && styles.unread, pressed && { opacity: 0.8 }]}>
              <IconBadge tone={item.read ? 'neutral' : 'info'} size={40}><Bell color={item.read ? color.primary : color.info} size={20} /></IconBadge>
              <View style={styles.flex}>
                <AppText variant="bodyMedium">{item.title}</AppText>
                <AppText variant="small" muted>{item.body}</AppText>
                <AppText variant="caption" muted>{t(key, { count })}</AppText>
              </View>
              {!item.read ? <View style={styles.dot} accessibilityLabel={t('notifications.unread')} /> : null}
            </Pressable>
          );
        }}
        ListEmptyComponent={list.isSuccess ? <EmptyState pose="wave" message={t('notifications.empty')} /> : null}
        ListFooterComponent={list.isFetchingNextPage ? <ActivityIndicator color={color.primary} /> : null}
        onEndReached={() => { if (list.hasNextPage && !list.isFetchingNextPage) void list.fetchNextPage(); }}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  list: { padding: space.xl, gap: space.md },
  row: {
    flexDirection: 'row', alignItems: 'flex-start', gap: space.md, padding: space.lg, borderRadius: radius.md,
    backgroundColor: color.surface, ...shadow,
  },
  unread: { backgroundColor: color.infoTint, borderColor: color.infoTint },
  dot: { width: 10, height: 10, borderRadius: 5, backgroundColor: color.danger, marginTop: 6 },
});
