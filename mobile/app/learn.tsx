/**
 * S32 Learn (wireframe "Jargon Explainer"): learning stats (XP, level, streak, lessons done), a
 * term search ("EMI, SIP, NAV…") with live results, popular-term chips, and lessons with category
 * filters (done ones ticked). Term -> S33, lesson -> S34.
 */
import { useState } from 'react';
import { Pressable, RefreshControl, StyleSheet, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { BookOpen, ChevronRight, CircleCheck, Clock, Flame, PiggyBank, Search, ShieldCheck, Star, TrendingUp, X, type LucideIcon } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { getLearnStats, listLessons, searchTerms, type LessonCategory, type LessonListItemDTO } from '@/api/endpoints';
import {
  AppText, Card, Chip, EmptyState, ErrorBanner, IconBadge, PageHeader, ProgressBar, Screen, SectionHeader, SkeletonCard,
} from '@/components';
import { learnKeys, lessonProgress, popularTerms, useDebounced, xpToNextLevel } from '@/features/learn/learn';
import { useLanguageStore } from '@/stores/language';
import { color, fontFor, MAX_FONT_SCALE, MIN_TOUCH, radius, space, toneColors, type Tone } from '@/theme';

const LESSON_CATEGORIES: LessonCategory[] = ['basics', 'savings', 'investing', 'insurance'];
const CATEGORY_ICON: Record<LessonCategory, { Icon: LucideIcon; tone: Tone }> = {
  basics: { Icon: BookOpen, tone: 'neutral' }, savings: { Icon: PiggyBank, tone: 'neutral' },
  investing: { Icon: TrendingUp, tone: 'neutral' }, insurance: { Icon: ShieldCheck, tone: 'neutral' },
};

export default function Learn() {
  const { t } = useTranslation();
  const language = useLanguageStore((s) => s.language);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<LessonCategory | 'all'>('all');
  const q = useDebounced(query.trim());

  const stats = useQuery({ queryKey: learnKeys.stats, queryFn: getLearnStats });
  const allTerms = useQuery({ queryKey: learnKeys.terms(language, ''), queryFn: () => searchTerms({ limit: 50 }), staleTime: 10 * 60_000 });
  const results = useQuery({ queryKey: learnKeys.terms(language, q), queryFn: () => searchTerms({ q, limit: 10 }), enabled: q.length > 0 });
  const lessons = useQuery({
    queryKey: learnKeys.lessons(language, category),
    queryFn: () => listLessons(category === 'all' ? undefined : category),
  });
  const s = stats.data;
  const refresh = () => { void stats.refetch(); void lessons.refetch(); void allTerms.refetch(); };

  return (
    <Screen back refreshControl={<RefreshControl refreshing={stats.isRefetching} onRefresh={refresh} />}>
      <PageHeader title={t('learn.title')} subtitle={t('learn.subtitle')} pose="point_up" />

      {s ? (
        <Card>
          <View style={styles.statsRow}>
            <Stat icon={<Star color={color.primary} size={18} />} tone="neutral" value={String(s.xp)} label={t('learn.xp')} />
            <Stat icon={<TrendingUp color={color.primary} size={18} />} tone="neutral" value={String(s.level)} label={t('learn.level')} />
            <Stat icon={<Flame color={color.primary} size={18} />} tone="neutral" value={String(s.streak_days)} label={t('learn.streak')} />
          </View>
          <View style={styles.between}>
            <AppText variant="small" muted>{t('learn.lessonsDone', { done: s.completed_lessons, total: s.total_lessons })}</AppText>
            <AppText variant="caption" muted>{t('learn.toNextLevel', { xp: xpToNextLevel(s.xp) })}</AppText>
          </View>
          <ProgressBar pct={lessonProgress(s.completed_lessons, s.total_lessons)} height={8} />
        </Card>
      ) : stats.isPending ? <SkeletonCard lines={2} /> : null}
      {stats.error ? <ErrorBanner error={stats.error} onRetry={() => void stats.refetch()} /> : null}

      <SectionHeader title={t('learn.jargon')} />
      <View style={styles.search}>
        <Search color={color.textMuted} size={20} />
        <TextInput value={query} onChangeText={setQuery} placeholder={t('learn.searchPlaceholder')} placeholderTextColor={color.textMuted}
          maxFontSizeMultiplier={MAX_FONT_SCALE} accessibilityLabel={t('learn.searchPlaceholder')} autoCorrect={false}
          style={[styles.searchInput, { fontFamily: fontFor(language, 'body') }]} />
        {query ? (
          <Pressable onPress={() => setQuery('')} accessibilityRole="button" accessibilityLabel={t('common.close')} hitSlop={8}>
            <X color={color.textMuted} size={18} />
          </Pressable>
        ) : null}
      </View>

      {q ? (
        <Card>
          {results.isPending ? <SkeletonCard lines={2} /> : null}
          {results.data && results.data.length === 0 ? <AppText muted>{t('learn.noTerms', { q })}</AppText> : null}
          {(results.data ?? []).map((term) => (
            <Pressable key={term.slug} onPress={() => router.push({ pathname: '/term/[slug]', params: { slug: term.slug } })} accessibilityRole="button"
              style={({ pressed }) => [styles.result, pressed && styles.pressed]}>
              <View style={styles.flex}>
                <AppText variant="bodyMedium">{term.term}</AppText>
                <AppText variant="small" muted numberOfLines={2}>{term.short}</AppText>
              </View>
              <ChevronRight color={color.textMuted} size={18} />
            </Pressable>
          ))}
        </Card>
      ) : (
        <View style={styles.chips}>
          <AppText variant="small" muted style={styles.full}>{t('learn.popular')}</AppText>
          {popularTerms(allTerms.data ?? []).map((term) => (
            <Chip key={term.slug} label={term.term} onPress={() => router.push({ pathname: '/term/[slug]', params: { slug: term.slug } })} />
          ))}
        </View>
      )}

      <SectionHeader title={t('learn.lessons')} />
      <View style={styles.chips}>
        {(['all', ...LESSON_CATEGORIES] as const).map((c) => (
          <Chip key={c} label={c === 'all' ? t('finance.filter.all') : t(`learn.category.${c}`)} selected={category === c} onPress={() => setCategory(c)} />
        ))}
      </View>
      {lessons.isPending ? <><SkeletonCard lines={2} /><SkeletonCard lines={2} /></> : null}
      {lessons.error ? <ErrorBanner error={lessons.error} onRetry={() => void lessons.refetch()} /> : null}
      {lessons.data && lessons.data.length === 0 ? <EmptyState pose="thinking" message={t('learn.noLessons')} /> : null}
      {(lessons.data ?? []).map((l) => <LessonCard key={l.id} lesson={l} />)}
    </Screen>
  );
}

function Stat({ icon, tone, value, label }: { icon: React.ReactNode; tone: Tone; value: string; label: string }) {
  return (
    <View style={styles.stat} accessible accessibilityLabel={`${label}: ${value}`}>
      <IconBadge tone={tone} size={36}>{icon}</IconBadge>
      <View>
        <AppText variant="h3">{value}</AppText>
        <AppText variant="caption" muted>{label}</AppText>
      </View>
    </View>
  );
}

function LessonCard({ lesson }: { lesson: LessonListItemDTO }) {
  const { t } = useTranslation();
  const { Icon, tone } = CATEGORY_ICON[lesson.category] ?? CATEGORY_ICON.basics;
  return (
    <Card onPress={() => router.push({ pathname: '/lesson/[id]', params: { id: lesson.id } })} accessibilityLabel={lesson.title} style={styles.lesson}>
      <IconBadge tone={tone} size={44}><Icon color={toneColors[tone].fg} size={22} /></IconBadge>
      <View style={styles.flex}>
        <AppText variant="bodyMedium" numberOfLines={2}>{lesson.title}</AppText>
        <View style={styles.meta}>
          <Clock color={color.textMuted} size={13} />
          <AppText variant="caption" muted>{t('learn.minutes', { count: lesson.duration_min })}</AppText>
          <AppText variant="caption" muted>{`· ${t(`learn.difficulty.${lesson.difficulty}`)}`}</AppText>
          <AppText variant="caption" tint={toneColors.warning.fg}>{`· +${lesson.xp_reward} XP`}</AppText>
        </View>
      </View>
      {lesson.completed ? <CircleCheck color={color.success} size={22} accessibilityLabel={t('learn.completed')} /> : <ChevronRight color={color.textMuted} size={18} />}
    </Card>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  full: { width: '100%' },
  between: { flexDirection: 'row', justifyContent: 'space-between', gap: space.sm, marginTop: space.xs },
  statsRow: { flexDirection: 'row', justifyContent: 'space-between', gap: space.sm },
  stat: { flexDirection: 'row', alignItems: 'center', gap: space.sm, flexShrink: 1 },
  search: {
    flexDirection: 'row', alignItems: 'center', gap: space.sm, minHeight: MIN_TOUCH + 4, paddingHorizontal: space.lg,
    borderRadius: radius.pill, backgroundColor: color.fill,
  },
  searchInput: { flex: 1, minWidth: 0, fontSize: 16, color: color.text, paddingVertical: space.md, outlineWidth: 0 } as object,
  result: { flexDirection: 'row', alignItems: 'center', gap: space.sm, paddingVertical: space.sm, minHeight: MIN_TOUCH },
  pressed: { opacity: 0.7 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
  lesson: { flexDirection: 'row', alignItems: 'center', gap: space.md },
  meta: { flexDirection: 'row', alignItems: 'center', gap: space.xs, flexWrap: 'wrap', marginTop: 2 },
});
