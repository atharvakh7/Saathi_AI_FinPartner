/**
 * Past conversations, newest first: tap to reopen in the Saathi tab, delete with confirmation
 * (memories learned from it stay, managed on the Memory screen).
 */
import { useState } from 'react';
import { FlatList, Pressable, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { useInfiniteQuery, useMutation } from '@tanstack/react-query';
import { MessageCircle, Trash2 } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { deleteConversation, listConversations, type ConversationDTO } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import { AppText, ConfirmDialog, EmptyState, ErrorBanner, IconBadge, Screen, SkeletonCard } from '@/components';
import { chatKeys } from '@/features/chat/chat';
import { relativeTime } from '@/lib/format';
import { useChatStore, useUiStore } from '@/stores';
import { color, MIN_TOUCH, shadow, space } from '@/theme';

export default function ChatHistory() {
  const { t } = useTranslation();
  const [confirm, setConfirm] = useState<ConversationDTO | null>(null);
  const convs = useInfiniteQuery({
    queryKey: [...chatKeys.conversations, 'all'],
    queryFn: ({ pageParam }) => listConversations(pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => last.next_cursor,
  });
  const items = convs.data?.pages.flatMap((p) => p.items) ?? [];
  const remove = useMutation({
    mutationFn: (id: string) => deleteConversation(id),
    onSuccess: (_d, id) => {
      if (useChatStore.getState().activeConversationId === id) useChatStore.getState().startNewChat();
      void queryClient.invalidateQueries({ queryKey: chatKeys.conversations });
      setConfirm(null);
      useUiStore.getState().showToast(t('finance.form.deleted'), 'success');
    },
  });
  const open = (id: string) => {
    useChatStore.getState().setActiveConversation(id);
    router.back();
  };

  return (
    <Screen title={t('chat.history')} back scroll={false} padded={false}>
      <FlatList
        data={items}
        keyExtractor={(c) => c.id}
        contentContainerStyle={styles.list}
        onEndReached={() => { if (convs.hasNextPage && !convs.isFetchingNextPage) void convs.fetchNextPage(); }}
        ListHeaderComponent={<>
          {convs.isPending ? <SkeletonCard lines={4} /> : null}
          {convs.error ? <ErrorBanner error={convs.error} onRetry={() => void convs.refetch()} /> : null}
        </>}
        ListEmptyComponent={convs.isSuccess ? <EmptyState pose="speaking" message={t('chat.historyEmpty')} /> : null}
        renderItem={({ item }) => {
          const [key, count] = relativeTime(item.last_message_at);
          return (
            <View style={styles.row}>
              <Pressable onPress={() => open(item.id)} accessibilityRole="button" style={({ pressed }) => [styles.main, pressed && styles.pressed]}>
                <IconBadge tone="neutral" size={40}><MessageCircle color={color.primary} size={20} /></IconBadge>
                <View style={styles.flex}>
                  <AppText variant="bodyMedium" numberOfLines={1}>{item.title || t('chat.untitled')}</AppText>
                  <AppText variant="caption" muted>{t(key, { count })}</AppText>
                </View>
              </Pressable>
              <Pressable onPress={() => setConfirm(item)} accessibilityRole="button" accessibilityLabel={t('common.delete')}
                hitSlop={6} style={styles.del}>
                <Trash2 color={color.danger} size={20} />
              </Pressable>
            </View>
          );
        }}
      />
      <ConfirmDialog visible={!!confirm} title={t('chat.deleteTitle')} message={t('chat.deleteMessage')} confirmLabel={t('common.delete')}
        danger loading={remove.isPending} onConfirm={() => confirm && remove.mutate(confirm.id)} onCancel={() => setConfirm(null)}>
        {remove.error ? <ErrorBanner error={remove.error} /> : null}
      </ConfirmDialog>
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  list: { padding: space.xl, gap: space.md },
  row: { flexDirection: 'row', alignItems: 'center', backgroundColor: color.surface, borderRadius: 18, ...shadow },
  main: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: space.md, padding: space.md },
  pressed: { opacity: 0.7 },
  del: { width: MIN_TOUCH, height: MIN_TOUCH, alignItems: 'center', justifyContent: 'center' },
});
