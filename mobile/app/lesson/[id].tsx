/**
 * S34 Lesson: title, minutes / difficulty / XP, Listen, video when there is one, the lesson text
 * (Markdown), and "Mark as complete" -> +XP (awarded once) with the new level and streak.
 */
import { useEffect } from 'react';
import { Linking, StyleSheet, View } from 'react-native';
import { Redirect, router, useLocalSearchParams } from 'expo-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { CircleCheck, Clock, PlayCircle, Sparkles, Square, Volume2 } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { completeLesson, getLesson } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import { AppText, Button, Card, EmptyState, ErrorBanner, Markdown, MascotBubble, Screen, SkeletonCard } from '@/components';
import { invalidateLearn, learnKeys } from '@/features/learn/learn';
import { usePlayback } from '@/features/voice/useVoice';
import { useUiStore } from '@/stores';
import { useLanguageStore } from '@/stores/language';
import { isLoggedIn, useSessionStore } from '@/stores/session';
import { color, space, toneColors } from '@/theme';

/** Markdown -> plain text for reading aloud. */
const plain = (md: string) => md.replace(/[#*_>`]/g, '').replace(/\n{2,}/g, '. ').replace(/\n/g, ' ');

export default function Lesson() {
  const { t } = useTranslation();
  const { id } = useLocalSearchParams<{ id: string }>();
  const loggedIn = useSessionStore(isLoggedIn);
  const language = useLanguageStore((s) => s.language);
  const lesson = useQuery({ queryKey: learnKeys.lesson(id, language), queryFn: () => getLesson(id), enabled: loggedIn });
  const playback = usePlayback();
  useEffect(() => () => playback.stop(), [playback.stop]);
  const complete = useMutation({
    mutationFn: () => completeLesson(id),
    onSuccess: (res) => {
      queryClient.setQueryData(learnKeys.lesson(id, language), (old: typeof lesson.data) => (old ? { ...old, completed: true } : old));
      invalidateLearn();
      useUiStore.getState().showToast(res.xp_awarded > 0
        ? t('learn.xpEarned', { xp: res.xp_awarded, streak: res.stats.streak_days })
        : t('learn.alreadyDone'), 'success');
    },
  });
  if (!loggedIn) return <Redirect href="/onboarding/welcome" />;
  const l = lesson.data;
  const speaking = playback.speakingId === `lesson-${id}`;

  return (
    <Screen title={t('learn.lesson')} back
      footer={l ? (
        l.completed
          ? <Button label={t('learn.completed')} variant="secondary" disabled icon={<CircleCheck color={color.success} size={18} />} />
          : <Button label={t('learn.markComplete', { xp: l.xp_reward })} loading={complete.isPending} onPress={() => complete.mutate()} />
      ) : undefined}>
      {lesson.isPending ? <><SkeletonCard lines={3} /><SkeletonCard lines={8} /></> : null}
      {lesson.error ? (
        lesson.error instanceof ApiError && lesson.error.code === 'NOT_FOUND'
          ? <EmptyState pose="thinking" message={t('errors.NOT_FOUND')} actionLabel={t('common.back')} onAction={() => router.back()} />
          : <ErrorBanner error={lesson.error} onRetry={() => void lesson.refetch()} />
      ) : null}
      {l ? (
        <>
          <AppText variant="h1">{l.title}</AppText>
          <View style={styles.meta}>
            <Clock color={color.textMuted} size={14} />
            <AppText variant="small" muted>{t('learn.minutes', { count: l.duration_min })}</AppText>
            <AppText variant="small" muted>{`· ${t(`learn.difficulty.${l.difficulty}`)}`}</AppText>
            <AppText variant="small" tint={toneColors.warning.fg}>{`· +${l.xp_reward} XP`}</AppText>
          </View>
          <View style={styles.actions}>
            <Button variant="secondary" size="sm" fullWidth={false} label={speaking ? t('common.stop') : t('common.listen')}
              icon={speaking ? <Square color={color.primary} size={16} /> : <Volume2 color={color.primary} size={18} />}
              onPress={() => playback.toggle(`lesson-${id}`, `${l.title}. ${plain(l.body_md)}`, l.language)} />
            {l.video ? (
              <Button size="sm" fullWidth={false} label={t('learn.watch', { sec: l.video.duration_sec })}
                icon={<PlayCircle color={color.onPrimary} size={18} />} onPress={() => void Linking.openURL(l.video!.url)} />
            ) : null}
          </View>
          {l.translation_source === 'llm' ? (
            <View style={styles.ai}>
              <Sparkles color={toneColors.info.fg} size={14} />
              <AppText variant="caption" tint={toneColors.info.fg}>{t('learn.simplifiedByAi')}</AppText>
            </View>
          ) : null}
          <Card><Markdown source={l.body_md} /></Card>
          {l.completed ? <MascotBubble pose="thumbs_up" size={72} text={t('learn.doneBubble')} /> : null}
          {complete.error ? <ErrorBanner error={complete.error} onRetry={() => complete.mutate()} /> : null}
        </>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  meta: { flexDirection: 'row', alignItems: 'center', gap: space.xs, flexWrap: 'wrap' },
  actions: { flexDirection: 'row', gap: space.sm, flexWrap: 'wrap' },
  ai: { flexDirection: 'row', alignItems: 'center', gap: space.xs },
});
