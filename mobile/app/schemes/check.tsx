/**
 * S24 Eligibility check: the questions that decide the most schemes, one at a time — Yes / No / Not
 * sure, a choice list, or a number — with "helps check N schemes" and a progress bar. Back goes to the
 * previous question; Finish (or the last answer) sends everything (POST /schemes/eligibility/check,
 * which also saves the answers to the profile; "Not sure" isn't saved) and opens the matches (S25).
 */
import { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Check } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { checkEligibility, getEligibilityQuestions, type QuestionDTO } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import { AppText, Button, Card, EmptyState, ErrorBanner, MascotBubble, ProgressBar, Screen, SkeletonCard, TextField } from '@/components';
import { invalidateSchemes, numberAnswer, optionKey, schemeKeys } from '@/features/schemes/schemes';
import { useLanguageStore } from '@/stores/language';
import { color, MIN_TOUCH, radius, shadow, space } from '@/theme';

type Answer = boolean | number | string | null;

export default function EligibilityCheck() {
  const { t } = useTranslation();
  const language = useLanguageStore((s) => s.language);
  const questions = useQuery({ queryKey: schemeKeys.questions, queryFn: getEligibilityQuestions, staleTime: Infinity });
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [numText, setNumText] = useState('');
  const send = useMutation({
    mutationFn: (all: Record<string, Answer>) => checkEligibility(all),
    onSuccess: (res) => {
      queryClient.setQueryData(schemeKeys.matches(language), res);
      invalidateSchemes();
      router.replace('/schemes/matches');
    },
  });
  const list = questions.data ?? [];
  const q: QuestionDTO | undefined = list[index];

  const answer = (value: Answer) => {
    if (!q) return;
    const next = { ...answers, [q.field]: value };
    setAnswers(next);
    setNumText('');
    if (index + 1 < list.length) setIndex(index + 1);
    else send.mutate(next);
  };

  return (
    <Screen title={t('schemes.checkTitle')} back={index > 0 ? () => setIndex(index - 1) : true}
      footer={list.length && Object.keys(answers).length ? (
        <Button label={t('schemes.seeResults')} variant="secondary" loading={send.isPending} onPress={() => send.mutate(answers)} />
      ) : undefined}>
      {questions.isPending ? <SkeletonCard lines={4} /> : null}
      {questions.error ? <ErrorBanner error={questions.error} onRetry={() => void questions.refetch()} /> : null}
      {questions.data && list.length === 0 ? (
        <EmptyState pose="thumbs_up" message={t('schemes.noQuestions')} actionLabel={t('schemes.seeMatches')}
          onAction={() => router.replace('/schemes/matches')} />
      ) : null}
      {q ? (
        <>
          <View style={styles.progress}>
            <AppText variant="caption" muted>{t('schemes.questionOf', { n: index + 1, total: list.length })}</AppText>
            <ProgressBar pct={(100 * index) / list.length} height={6} />
          </View>
          <MascotBubble pose="thinking" size={72} text={t(`eligibility.q.${q.field}`)} />
          <AppText variant="caption" muted align="center">{t('schemes.affects', { count: q.affects_count })}</AppText>

          {q.type === 'boolean' ? (
            <View style={styles.answers}>
              <Choice label={t('common.yes')} onPress={() => answer(true)} selected={answers[q.field] === true} />
              <Choice label={t('common.no')} onPress={() => answer(false)} selected={answers[q.field] === false} />
            </View>
          ) : null}
          {q.type === 'enum' ? (
            <Card style={styles.options}>
              {(q.options ?? []).map((o) => (
                <Choice key={o} label={t(optionKey(q.field, o))} onPress={() => answer(o)} selected={answers[q.field] === o} />
              ))}
            </Card>
          ) : null}
          {q.type === 'number' ? (
            <View style={styles.number}>
              <TextField label={t(`eligibility.field.${q.field}`)} value={numText} onChangeText={setNumText} keyboardType="number-pad"
                prefix={/income/.test(q.field) ? '₹' : undefined} maxLength={12}
                error={numText && numberAnswer(numText) === null ? t('form.range') : null} />
              <Button label={t('common.next')} disabled={numberAnswer(numText) === null} onPress={() => answer(numberAnswer(numText))} />
            </View>
          ) : null}
          <Button label={t('common.notSure')} variant="ghost" onPress={() => answer(null)} />
          {send.error ? <ErrorBanner error={send.error} onRetry={() => send.mutate(answers)} /> : null}
        </>
      ) : null}
    </Screen>
  );
}

function Choice({ label, onPress, selected }: { label: string; onPress: () => void; selected?: boolean }) {
  return (
    <Pressable onPress={onPress} accessibilityRole="radio" accessibilityState={{ checked: !!selected }}
      style={({ pressed }) => [styles.choice, selected && styles.choiceOn, pressed && { opacity: 0.8 }]}>
      <AppText variant="bodyMedium" style={styles.flex} tint={selected ? color.primary : color.text}>{label}</AppText>
      {selected ? <Check color={color.primary} size={20} /> : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  progress: { gap: space.xs },
  answers: { gap: space.sm },
  options: { gap: space.sm },
  number: { gap: space.md },
  choice: {
    flexDirection: 'row', alignItems: 'center', minHeight: MIN_TOUCH + 8, paddingHorizontal: space.lg, borderRadius: radius.md,
    borderWidth: 1.5, borderColor: 'transparent', backgroundColor: color.surface, ...shadow,
  },
  choiceOn: { borderColor: color.primary, backgroundColor: color.primaryTint },
});
