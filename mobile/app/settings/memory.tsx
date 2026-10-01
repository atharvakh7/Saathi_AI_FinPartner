/** S40 Memory Manager (spec §4.7): remembered facts, delete one, or forget everything. */
import { useState } from 'react';
import { Pressable, RefreshControl, StyleSheet, View } from 'react-native';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Trash2 } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { deleteMemoryFact, forgetEverything, listMemory, type MemoryFactDTO } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import { AppText, Button, Card, Chip, ConfirmDialog, EmptyState, ErrorBanner, MascotBubble, Screen, SkeletonCard } from '@/components';
import { displayDate } from '@/lib/format';
import { useUiStore } from '@/stores';
import { color, MIN_TOUCH, space } from '@/theme';

const KEY = ['memory'];

export default function Memory() {
  const { t } = useTranslation();
  const facts = useQuery({ queryKey: KEY, queryFn: listMemory });
  const [confirm, setConfirm] = useState<MemoryFactDTO | 'all' | null>(null);

  const removeOne = useMutation({
    mutationFn: (id: string) => deleteMemoryFact(id),
    onSuccess: (_d, id) => {
      queryClient.setQueryData<MemoryFactDTO[]>(KEY, (old) => old?.filter((f) => f.id !== id));
      setConfirm(null);
      useUiStore.getState().showToast(t('settings.memory.forgotOne'), 'success');
    },
  });
  const removeAll = useMutation({
    mutationFn: forgetEverything,
    onSuccess: () => {
      queryClient.setQueryData<MemoryFactDTO[]>(KEY, []);
      setConfirm(null);
      useUiStore.getState().showToast(t('settings.memory.forgotAll'), 'success');
    },
  });
  const list = facts.data ?? [];

  return (
    <Screen title={t('settings.memory.title')} back
      refreshControl={<RefreshControl refreshing={facts.isRefetching} onRefresh={() => void facts.refetch()} />}
      footer={list.length ? (
        <Button label={t('settings.memory.forgetAll')} variant="danger" onPress={() => setConfirm('all')} />
      ) : undefined}>
      <MascotBubble pose="thinking" text={t('settings.memory.intro')} size={80} />
      {facts.isPending ? <SkeletonCard lines={4} /> : null}
      {facts.error ? <ErrorBanner error={facts.error} onRetry={() => void facts.refetch()} /> : null}
      {facts.data && list.length === 0 ? <EmptyState pose="thinking" message={t('settings.memory.empty')} /> : null}
      {list.map((f) => (
        <Card key={f.id} style={styles.fact}>
          <View style={styles.flex}>
            <AppText>{f.fact_text}</AppText>
            <View style={styles.meta}>
              <Chip label={t(`settings.memory.category.${f.category}`)} />
              <AppText variant="caption" muted>{displayDate(f.created_at)}</AppText>
            </View>
          </View>
          <Pressable onPress={() => setConfirm(f)} accessibilityRole="button" accessibilityLabel={t('common.delete')}
            hitSlop={8} style={styles.delete}>
            <Trash2 color={color.danger} size={20} />
          </Pressable>
        </Card>
      ))}
      {removeOne.error ? <ErrorBanner error={removeOne.error} /> : null}
      {removeAll.error ? <ErrorBanner error={removeAll.error} /> : null}

      <ConfirmDialog
        visible={confirm !== null}
        title={confirm === 'all' ? t('settings.memory.forgetAllTitle') : t('settings.memory.forgetOneTitle')}
        message={confirm === 'all' ? t('settings.memory.forgetAllWarning') : confirm?.fact_text}
        confirmLabel={t('common.delete')}
        danger
        loading={removeOne.isPending || removeAll.isPending}
        onConfirm={() => (confirm === 'all' ? removeAll.mutate() : confirm && removeOne.mutate(confirm.id))}
        onCancel={() => setConfirm(null)}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  fact: { flexDirection: 'row', alignItems: 'flex-start', gap: space.sm },
  meta: { flexDirection: 'row', alignItems: 'center', gap: space.sm, marginTop: space.sm, flexWrap: 'wrap' },
  delete: { minWidth: MIN_TOUCH, minHeight: MIN_TOUCH, alignItems: 'center', justifyContent: 'center' },
});
