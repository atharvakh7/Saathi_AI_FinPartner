/**
 * S33 Term detail: the term (and its English name), meaning, example, "think of it like…", key
 * takeaway, Listen, video when there is one, related terms, "Was this helpful?". Viewing a term counts
 * as learning activity (streak). Machine translations carry a "Simplified by AI" note.
 */
import { useEffect, useState } from 'react';
import { Linking, StyleSheet, View } from 'react-native';
import { Redirect, router, useLocalSearchParams } from 'expo-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Lightbulb, MessageCircle, PlayCircle, Sparkles, ThumbsDown, ThumbsUp, Volume2, Square } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { getTerm, termFeedback } from '@/api/endpoints';
import { AppText, Button, Card, Chip, EmptyState, ErrorBanner, IconBadge, Screen, SectionHeader, SkeletonCard } from '@/components';
import { invalidateLearn, learnKeys } from '@/features/learn/learn';
import { usePlayback } from '@/features/voice/useVoice';
import { useLanguageStore } from '@/stores/language';
import { isLoggedIn, useSessionStore } from '@/stores/session';
import { color, radius, space, toneColors } from '@/theme';

export default function TermDetail() {
  const { t } = useTranslation();
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const loggedIn = useSessionStore(isLoggedIn);
  const language = useLanguageStore((s) => s.language);
  const term = useQuery({ queryKey: learnKeys.term(slug, language), queryFn: () => getTerm(slug), enabled: loggedIn });
  const [voted, setVoted] = useState<boolean | null>(null);
  const playback = usePlayback();
  useEffect(() => { if (term.isSuccess) invalidateLearn(); }, [term.isSuccess]); // viewing counts toward the streak
  useEffect(() => () => playback.stop(), [playback.stop]);
  const feedback = useMutation({ mutationFn: (helpful: boolean) => termFeedback(slug, helpful), onSuccess: (_d, v) => setVoted(v) });
  if (!loggedIn) return <Redirect href="/onboarding/welcome" />;
  const d = term.data;
  const speaking = playback.speakingId === `term-${slug}`;

  return (
    <Screen title={d?.term ?? t('learn.jargon')} back>
      {term.isPending ? <SkeletonCard lines={6} /> : null}
      {term.error ? (
        term.error instanceof ApiError && term.error.code === 'NOT_FOUND'
          ? <EmptyState pose="thinking" message={t('errors.NOT_FOUND')} actionLabel={t('common.back')} onAction={() => router.back()} />
          : <ErrorBanner error={term.error} onRetry={() => void term.refetch()} />
      ) : null}
      {d ? (
        <>
          <Card>
            <View style={styles.row}>
              <View style={styles.flex}>
                <AppText variant="h1">{d.term}</AppText>
                {d.term_en && d.term_en !== d.term ? <AppText muted textLanguage="en">{d.term_en}</AppText> : null}
              </View>
              <Chip label={t(`learn.glossaryCategory.${d.category}`)} />
            </View>
            <AppText>{d.definition}</AppText>
            <Button variant="secondary" size="sm" fullWidth={false}
              label={speaking ? t('common.stop') : t('common.listen')}
              icon={speaking ? <Square color={color.primary} size={16} /> : <Volume2 color={color.primary} size={18} />}
              onPress={() => playback.toggle(`term-${slug}`, `${d.term}. ${d.definition} ${d.example}`, d.language)} />
            {d.translation_source === 'llm' ? (
              <View style={styles.ai}>
                <Sparkles color={toneColors.info.fg} size={14} />
                <AppText variant="caption" tint={toneColors.info.fg}>{t('learn.simplifiedByAi')}</AppText>
              </View>
            ) : null}
          </Card>

          {d.video ? (
            <Button label={t('learn.watch', { sec: d.video.duration_sec })} icon={<PlayCircle color={color.onPrimary} size={20} />}
              onPress={() => void Linking.openURL(d.video!.url)} />
          ) : null}

          {d.example ? (
            <Card>
              <SectionHeader title={t('learn.example')} />
              <AppText>{d.example}</AppText>
            </Card>
          ) : null}
          {d.analogy ? (
            <Card style={styles.analogy}>
              <IconBadge tone="warning" size={36}><Lightbulb color={toneColors.warning.fg} size={18} /></IconBadge>
              <View style={styles.flex}>
                <AppText variant="bodyMedium">{t('learn.thinkOfIt')}</AppText>
                <AppText>{d.analogy}</AppText>
              </View>
            </Card>
          ) : null}
          {d.key_takeaway ? (
            <View style={[styles.takeaway, { backgroundColor: toneColors.neutral.bg }]}>
              <AppText variant="small" tint={color.primary}>{t('learn.remember')}</AppText>
              <AppText variant="bodyMedium" tint={color.primary}>{d.key_takeaway}</AppText>
            </View>
          ) : null}

          {d.related.length ? (
            <>
              <SectionHeader title={t('learn.related')} />
              <View style={styles.chips}>
                {d.related.map((r) => <Chip key={r.slug} label={r.term} onPress={() => router.push({ pathname: '/term/[slug]', params: { slug: r.slug } })} />)}
              </View>
            </>
          ) : null}

          <Card>
            <AppText variant="small">{voted === null ? t('learn.helpful') : t('learn.thanks')}</AppText>
            {voted === null ? (
              <View style={styles.row}>
                <Button label={t('common.yes')} variant="secondary" size="sm" style={styles.flex} loading={feedback.isPending && feedback.variables}
                  icon={<ThumbsUp color={color.primary} size={16} />} onPress={() => feedback.mutate(true)} />
                <Button label={t('common.no')} variant="secondary" size="sm" style={styles.flex} loading={feedback.isPending && !feedback.variables}
                  icon={<ThumbsDown color={color.primary} size={16} />} onPress={() => feedback.mutate(false)} />
              </View>
            ) : null}
          </Card>
          <Button label={t('learn.askSaathi')} variant="ghost" icon={<MessageCircle color={color.primary} size={18} />}
            onPress={() => router.push('/saathi')} />
        </>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  row: { flexDirection: 'row', alignItems: 'center', gap: space.md },
  ai: { flexDirection: 'row', alignItems: 'center', gap: space.xs },
  analogy: { flexDirection: 'row', gap: space.md, alignItems: 'flex-start' },
  takeaway: { padding: space.lg, borderRadius: radius.md, gap: space.xs },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
});
