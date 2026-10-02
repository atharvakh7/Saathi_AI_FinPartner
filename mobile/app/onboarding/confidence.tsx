/** S08 Confidence Assessment: 5 questions, one per page, 1–5 scale; Skip sends [] (spec §4.7). */
import { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';

import { postConfidence } from '@/api/endpoints';
import { AppText, Button, ErrorBanner, Mascot, Screen } from '@/components';
import { queryClient } from '@/api/queryClient';
import { ME_KEY, nextOnboardingRoute } from '@/lib/session';
import { color, MIN_TOUCH, radius, space } from '@/theme';

const QUESTIONS = 5;

export default function Confidence() {
  const { t } = useTranslation();
  const retake = useLocalSearchParams<{ retake?: string }>().retake === '1'; // from Profile (S35)
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<(number | null)[]>(Array(QUESTIONS).fill(null));
  const current = answers[index] ?? null;
  const last = index === QUESTIONS - 1;

  const submit = useMutation({
    mutationFn: (values: number[]) => postConfidence(values),
    onSuccess: async () => {
      if (retake) {
        await queryClient.invalidateQueries({ queryKey: ME_KEY });
        router.back();
      } else router.replace((await nextOnboardingRoute()) as never);
    },
  });

  return (
    <Screen
      back={index > 0 ? () => setIndex(index - 1) : retake ? true : undefined}
      right={retake ? undefined : <Button label={t('common.skip')} variant="ghost" size="sm" fullWidth={false} onPress={() => submit.mutate([])} />}
      footer={
        <Button label={last ? t('onboarding.confidence.finish') : t('common.next')} disabled={current === null}
          loading={submit.isPending}
          onPress={() => (last ? submit.mutate(answers as number[]) : setIndex(index + 1))} />
      }>
      <View style={styles.center}>
        <Mascot pose="thinking" size={110} variant="bust" />
        <AppText variant="caption" muted>{t('onboarding.confidence.progress', { n: index + 1, total: QUESTIONS })}</AppText>
        <AppText variant="h2" align="center">{t(`onboarding.confidence.q${index + 1}`)}</AppText>
      </View>
      <View style={styles.scale} accessibilityRole="radiogroup">
        {[1, 2, 3, 4, 5].map((n) => {
          const on = current === n;
          return (
            <Pressable key={n} accessibilityRole="radio" accessibilityState={{ checked: on }}
              accessibilityLabel={`${n}${n === 1 ? `, ${t('onboarding.confidence.low')}` : n === 5 ? `, ${t('onboarding.confidence.high')}` : ''}`}
              onPress={() => setAnswers((a) => a.map((v, i) => (i === index ? n : v)))}
              style={[styles.point, on && styles.pointOn]}>
              <AppText variant="h3" tint={on ? color.onPrimary : color.primary}>{String(n)}</AppText>
            </Pressable>
          );
        })}
      </View>
      <View style={styles.ends}>
        <AppText variant="caption" muted>{t('onboarding.confidence.low')}</AppText>
        <AppText variant="caption" muted>{t('onboarding.confidence.high')}</AppText>
      </View>
      {submit.error ? <ErrorBanner error={submit.error} onRetry={() => submit.mutate(answers.every((a) => a !== null) ? (answers as number[]) : [])} /> : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  center: { alignItems: 'center', gap: space.md, paddingTop: space.lg },
  scale: { flexDirection: 'row', justifyContent: 'space-between', gap: space.sm, marginTop: space.xl },
  point: {
    flex: 1, minHeight: MIN_TOUCH + 8, borderRadius: radius.md, borderWidth: 1.5, borderColor: color.primary,
    alignItems: 'center', justifyContent: 'center', backgroundColor: color.surface,
  },
  pointOn: { backgroundColor: color.primary },
  ends: { flexDirection: 'row', justifyContent: 'space-between' },
});
