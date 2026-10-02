/**
 * S23 Scheme Scout (wireframe "Scheme Scout"): "Your profile match — N schemes found" with the top
 * matches, Check my eligibility (S24), search, and the categories as a 2-column grid (-> S26 list).
 */
import { useState } from 'react';
import { Pressable, RefreshControl, StyleSheet, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { ClipboardCheck, Search } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { getEligibilityQuestions, getSchemeCategories, getSchemeMatches } from '@/api/endpoints';
import { AppText, Button, Card, ErrorBanner, IconBadge, PageHeader, Screen, SectionHeader, SkeletonCard } from '@/components';
import { CATEGORY_ICON, DEFAULT_CATEGORY, SchemeRow } from '@/features/schemes/parts';
import { groupMatches, schemeKeys } from '@/features/schemes/schemes';
import { useLanguageStore } from '@/stores/language';
import { color, fontFor, MAX_FONT_SCALE, MIN_TOUCH, radius, space, shadow, toneColors } from '@/theme';

export default function SchemeScout() {
  const { t } = useTranslation();
  const language = useLanguageStore((s) => s.language);
  const [q, setQ] = useState('');
  const matches = useQuery({ queryKey: schemeKeys.matches(language), queryFn: getSchemeMatches });
  const categories = useQuery({ queryKey: schemeKeys.categories, queryFn: getSchemeCategories, staleTime: 10 * 60_000 });
  const questions = useQuery({ queryKey: schemeKeys.questions, queryFn: getEligibilityQuestions });
  const g = groupMatches(matches.data?.items ?? []);
  const top = [...g.eligible, ...g.possibly].slice(0, 4);
  const search = () => { if (q.trim()) router.push({ pathname: '/schemes/list', params: { q: q.trim() } }); };

  return (
    <Screen back refreshControl={<RefreshControl refreshing={matches.isRefetching} onRefresh={() => void matches.refetch()} />}>
      <PageHeader title={t('schemes.title')} subtitle={t('schemes.subtitle')} pose="point_up" />

      <View style={styles.matches}>
        <SectionHeader title={t('schemes.profileMatch')} action={matches.data?.total ? t('home.viewAll') : undefined}
          onAction={() => router.push('/schemes/matches')} />
        {matches.isPending ? <SkeletonCard lines={3} /> : null}
        {matches.error ? <ErrorBanner error={matches.error} onRetry={() => void matches.refetch()} /> : null}
        {matches.data ? (
          <AppText variant="small" muted>
            {t('schemes.found', { eligible: matches.data.eligible_count, possibly: matches.data.possibly_eligible_count })}
          </AppText>
        ) : null}
        {top.map((m) => <SchemeRow key={m.scheme.id} scheme={m.scheme} match={m} />)}
      </View>

      {questions.data && questions.data.length ? (
        <Card style={styles.check}>
          <IconBadge tone="positive" size={44}><ClipboardCheck color={color.success} size={22} /></IconBadge>
          <View style={styles.flex}>
            <AppText variant="bodyMedium">{t('schemes.checkTitle')}</AppText>
            <AppText variant="small" muted>{t('schemes.checkHint', { count: questions.data.length })}</AppText>
          </View>
        </Card>
      ) : null}
      {questions.data && questions.data.length ? (
        <Button label={t('schemes.checkButton')} onPress={() => router.push('/schemes/check')} />
      ) : null}

      <View style={styles.search}>
        <Search color={color.textMuted} size={20} />
        <TextInput value={q} onChangeText={setQ} onSubmitEditing={search} returnKeyType="search" placeholder={t('schemes.searchPlaceholder')}
          placeholderTextColor={color.textMuted} maxFontSizeMultiplier={MAX_FONT_SCALE} accessibilityLabel={t('schemes.searchPlaceholder')}
          style={[styles.searchInput, { fontFamily: fontFor(language, 'body') }]} />
      </View>

      <SectionHeader title={t('schemes.categories')} action={t('home.viewAll')} onAction={() => router.push('/schemes/list')} />
      {categories.isPending ? <SkeletonCard lines={3} /> : null}
      <View style={styles.grid}>
        {(categories.data ?? []).map((c) => {
          const { Icon, tone } = CATEGORY_ICON[c.slug] ?? DEFAULT_CATEGORY;
          return (
            <Pressable key={c.slug} onPress={() => router.push({ pathname: '/schemes/list', params: { category: c.slug } })}
              accessibilityRole="button" accessibilityLabel={t(`category.${c.slug}`)} style={({ pressed }) => [styles.tile, pressed && styles.pressed]}>
              <IconBadge tone={tone} size={40}><Icon color={toneColors[tone].fg} size={20} /></IconBadge>
              <View style={styles.flex}>
                <AppText variant="bodyMedium" numberOfLines={2}>{t(`category.${c.slug}`)}</AppText>
                <AppText variant="caption" muted>{t('schemes.count', { count: c.count })}</AppText>
              </View>
            </Pressable>
          );
        })}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  matches: { gap: space.md },
  check: { flexDirection: 'row', alignItems: 'center', gap: space.md },
  search: {
    flexDirection: 'row', alignItems: 'center', gap: space.sm, minHeight: MIN_TOUCH + 4, paddingHorizontal: space.lg,
    borderRadius: radius.pill, backgroundColor: color.fill,
  },
  searchInput: { flex: 1, minWidth: 0, fontSize: 16, color: color.text, paddingVertical: space.md, outlineWidth: 0 } as object,
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
  tile: {
    width: '48%', flexGrow: 1, flexDirection: 'row', alignItems: 'center', gap: space.sm, padding: space.md, minHeight: 72,
    borderRadius: radius.md, backgroundColor: color.surface, ...shadow,
  },
  pressed: { opacity: 0.7 },
});
