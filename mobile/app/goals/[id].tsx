/**
 * S18 Goal Detail: progress ring, saved / target / left, projection sentence, Add money | Withdraw
 * (amount + optional note), Pause / Resume, Edit, Delete (the emergency-fund goal can't be deleted),
 * and the latest contributions.
 */
import { useState } from 'react';
import { RefreshControl, StyleSheet, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Minus, Pause, Pencil, Play, Plus, Trash2 } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { addContribution, deleteGoal, getGoal, updateGoal, type GoalDetailDTO } from '@/api/endpoints';
import {
  AmountInput, AppText, Button, Card, ConfirmDialog, EmptyState, ErrorBanner, MascotBubble, ProgressRing, Screen,
  SectionHeader, SkeletonCard, TextField,
} from '@/components';
import { GoalIcon } from '@/features/goals/GoalCard';
import { goalKeys, invalidateGoals, projectionMessage } from '@/features/goals/goals';
import { dayLabel, displayDate, inr } from '@/lib/format';
import { useUiStore } from '@/stores';
import { color, MIN_TOUCH, space, toneColors } from '@/theme';

type Sheet = 'add' | 'withdraw' | null;

export default function GoalDetail() {
  const { t } = useTranslation();
  const { id } = useLocalSearchParams<{ id: string }>();
  const goal = useQuery({ queryKey: goalKeys.detail(id), queryFn: () => getGoal(id) });

  return (
    <Screen title={goal.data?.title ?? t('goals.title')} back
      right={goal.data && goal.data.status !== 'cancelled' ? (
        <Button label={t('common.edit')} variant="ghost" size="sm" fullWidth={false}
          icon={<Pencil color={color.primary} size={16} />} onPress={() => router.push({ pathname: '/goals/edit', params: { id } })} />
      ) : undefined}
      refreshControl={<RefreshControl refreshing={goal.isRefetching} onRefresh={() => void goal.refetch()} />}>
      {goal.isPending ? <><SkeletonCard lines={5} /><SkeletonCard /></> : null}
      {goal.error ? (
        goal.error instanceof ApiError && goal.error.code === 'NOT_FOUND'
          ? <EmptyState pose="thinking" message={t('errors.NOT_FOUND')} actionLabel={t('common.back')} onAction={() => router.back()} />
          : <ErrorBanner error={goal.error} onRetry={() => void goal.refetch()} />
      ) : null}
      {goal.data ? <Body goal={goal.data} /> : null}
    </Screen>
  );
}

function Body({ goal }: { goal: GoalDetailDTO }) {
  const { t } = useTranslation();
  const [sheet, setSheet] = useState<Sheet>(null);
  const [amount, setAmount] = useState<number | null>(null);
  const [note, setNote] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(false);
  const left = Math.max(0, goal.target_amount_inr - goal.current_amount_inr);
  const msg = projectionMessage(goal);
  const msgText = t(msg.key, {
    date: 'date' in msg ? displayDate(msg.date) : '', amount: 'amount' in msg ? inr(msg.amount) : '',
    rate: 'rate' in msg ? inr(msg.rate) : '',
  });
  const msgTone = msg.key === 'goals.proj.done' || msg.key === 'goals.proj.onTrack' ? 'positive'
    : msg.key === 'goals.proj.behind' || msg.key === 'goals.proj.paused' ? 'warning' : 'info';

  const contribute = useMutation({
    mutationFn: () => addContribution(goal.id, sheet === 'withdraw' ? -amount! : amount!, note.trim() || null),
    onSuccess: (g) => {
      invalidateGoals();
      setSheet(null);
      useUiStore.getState().showToast(
        g.status === 'completed' ? t('goals.reached') : sheet === 'withdraw' ? t('goals.withdrawn') : t('goals.added'), 'success');
    },
  });
  const setStatus = useMutation({
    mutationFn: (status: 'active' | 'paused') => updateGoal(goal.id, { status }),
    onSuccess: () => invalidateGoals(),
    onError: (e) => useUiStore.getState().showToast(e instanceof ApiError ? e.message : t('errors.INTERNAL'), 'error'),
  });
  const remove = useMutation({
    mutationFn: () => deleteGoal(goal.id),
    onSuccess: () => {
      invalidateGoals();
      setConfirmDelete(false);
      useUiStore.getState().showToast(t('finance.form.deleted'), 'success');
      router.back();
    },
  });
  const open = (s: Sheet) => {
    setAmount(null);
    setNote('');
    contribute.reset();
    setSheet(s);
  };
  const tooMuch = sheet === 'withdraw' && amount !== null && amount > goal.current_amount_inr;

  return (
    <>
      <Card style={styles.hero}>
        <View style={styles.heroTop}>
          <GoalIcon category={goal.category} />
          <View style={styles.flex}>
            <AppText variant="bodyMedium" numberOfLines={2}>{goal.title}</AppText>
            <AppText variant="caption" muted>
              {goal.target_date ? t('goals.byDate', { date: displayDate(goal.target_date) }) : t('onboarding.goals.noDate')}
            </AppText>
          </View>
        </View>
        <ProgressRing pct={goal.progress_pct} size={160} stroke={14} tint={goal.status === 'paused' ? color.warning : color.success}
          label={t('goals.pctComplete', { pct: goal.progress_pct })} />
        <View style={styles.stats}>
          <Stat label={t('goals.saved')} value={inr(goal.current_amount_inr)} tint={color.success} />
          <Stat label={t('goals.target')} value={inr(goal.target_amount_inr)} />
          <Stat label={t('goals.left')} value={inr(left)} />
        </View>
        <View style={[styles.msg, { backgroundColor: toneColors[msgTone].bg }]}>
          <AppText variant="small" tint={toneColors[msgTone].fg}>{msgText}</AppText>
        </View>
      </Card>

      {goal.status === 'completed' ? <MascotBubble pose="thumbs_up" text={t('goals.completedBubble')} size={80} /> : null}

      {goal.status !== 'cancelled' ? (
        <View style={styles.actions}>
          <Button label={t('goals.addMoney')} icon={<Plus color={color.onPrimary} size={18} />} style={styles.flex}
            onPress={() => open('add')} />
          <Button label={t('goals.withdraw')} variant="secondary" icon={<Minus color={color.primary} size={18} />} style={styles.flex}
            disabled={goal.current_amount_inr <= 0} onPress={() => open('withdraw')} />
        </View>
      ) : null}

      <SectionHeader title={t('goals.history')} />
      {goal.contributions.length === 0 ? <AppText variant="small" muted>{t('goals.noHistory')}</AppText> : null}
      {goal.contributions.length ? (
        <Card>
          {goal.contributions.map((c) => {
            const label = dayLabel(c.contributed_on);
            const plus = c.amount_inr > 0;
            return (
              <View key={c.id} style={styles.contribution}>
                <View style={styles.flex}>
                  <AppText variant="small">{label.key ? t(label.key) : label.text}</AppText>
                  {c.note ? <AppText variant="caption" muted numberOfLines={1}>{c.note}</AppText> : null}
                </View>
                <AppText variant="bodyMedium" tint={plus ? color.success : color.danger}>
                  {`${plus ? '+' : '−'}${inr(Math.abs(c.amount_inr))}`}
                </AppText>
              </View>
            );
          })}
        </Card>
      ) : null}

      {goal.status === 'active' || goal.status === 'paused' ? (
        <Button variant="ghost" loading={setStatus.isPending}
          icon={goal.status === 'active' ? <Pause color={color.primary} size={18} /> : <Play color={color.primary} size={18} />}
          label={goal.status === 'active' ? t('goals.pause') : t('goals.resume')}
          onPress={() => setStatus.mutate(goal.status === 'active' ? 'paused' : 'active')} />
      ) : null}
      <Button variant="ghost" label={t('goals.delete')} icon={<Trash2 color={color.danger} size={18} />}
        onPress={() => { remove.reset(); setConfirmDelete(true); }} />

      <ConfirmDialog visible={sheet !== null} title={sheet === 'withdraw' ? t('goals.withdraw') : t('goals.addMoney')}
        message={sheet === 'withdraw' ? t('goals.withdrawHint', { amount: inr(goal.current_amount_inr) }) : undefined}
        confirmLabel={t('common.save')} loading={contribute.isPending}
        confirmDisabled={!amount || amount <= 0 || tooMuch}
        onConfirm={() => contribute.mutate()} onCancel={() => setSheet(null)}>
        <AmountInput label={t('finance.form.amount')} value={amount} onChange={setAmount}
          error={tooMuch ? t('goals.tooMuch') : null} />
        <TextField label={`${t('finance.form.note')} (${t('common.optional')})`} value={note} onChangeText={setNote} maxLength={200} />
        {contribute.error ? <ErrorBanner error={contribute.error} /> : null}
      </ConfirmDialog>

      <ConfirmDialog visible={confirmDelete} title={t('goals.deleteTitle')} message={t('goals.deleteMessage')}
        confirmLabel={t('common.delete')} danger loading={remove.isPending}
        onConfirm={() => remove.mutate()} onCancel={() => setConfirmDelete(false)}>
        {remove.error ? (
          <ErrorBanner error={remove.error} message={remove.error instanceof ApiError && remove.error.code === 'CONFLICT'
            ? t('goals.efNoDelete') : undefined} />
        ) : null}
      </ConfirmDialog>
    </>
  );
}

function Stat({ label, value, tint }: { label: string; value: string; tint?: string }) {
  return (
    <View style={styles.stat}>
      <AppText variant="caption" muted>{label}</AppText>
      <AppText variant="bodyMedium" tint={tint} numberOfLines={1} adjustsFontSizeToFit>{value}</AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  hero: { alignItems: 'center', gap: space.lg },
  heroTop: { flexDirection: 'row', alignItems: 'center', gap: space.md, alignSelf: 'stretch' },
  stats: { flexDirection: 'row', alignSelf: 'stretch', gap: space.sm },
  stat: { flex: 1, alignItems: 'center', gap: 2, minWidth: 0 },
  msg: { alignSelf: 'stretch', padding: space.md, borderRadius: 12 },
  actions: { flexDirection: 'row', gap: space.md },
  contribution: { flexDirection: 'row', alignItems: 'center', gap: space.md, minHeight: MIN_TOUCH },
});
