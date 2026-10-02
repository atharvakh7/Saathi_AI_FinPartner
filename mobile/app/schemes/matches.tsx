/**
 * S25 Your matches: eligible, then possibly eligible (with what's still needed), and — on request —
 * "Show schemes I don't qualify for" with the reason. Answer more questions to firm up "possibly".
 */
import { useState } from 'react';
import { RefreshControl, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';

import { getSchemeMatches } from '@/api/endpoints';
import { AppText, Button, EmptyState, ErrorBanner, MascotBubble, Screen, SectionHeader, SkeletonCard } from '@/components';
import { SchemeRow } from '@/features/schemes/parts';
import { groupMatches, schemeKeys } from '@/features/schemes/schemes';
import { useLanguageStore } from '@/stores/language';
import { space } from '@/theme';

export default function Matches() {
  const { t } = useTranslation();
  const language = useLanguageStore((s) => s.language);
  const [showNot, setShowNot] = useState(false);
  const matches = useQuery({ queryKey: schemeKeys.matches(language), queryFn: getSchemeMatches });
  const g = groupMatches(matches.data?.items ?? []);

  return (
    <Screen title={t('schemes.matchesTitle')} back
      refreshControl={<RefreshControl refreshing={matches.isRefetching} onRefresh={() => void matches.refetch()} />}>
      {matches.isPending ? <><SkeletonCard lines={3} /><SkeletonCard lines={3} /></> : null}
      {matches.error ? <ErrorBanner error={matches.error} onRetry={() => void matches.refetch()} /> : null}
      {matches.data ? (
        <MascotBubble pose={matches.data.total ? 'thumbs_up' : 'thinking'} size={72}
          text={matches.data.total ? t('schemes.found', { eligible: matches.data.eligible_count, possibly: matches.data.possibly_eligible_count }) : t('schemes.noneYet')} />
      ) : null}
      {g.possibly.length ? (
        <Button label={t('schemes.answerMore')} variant="secondary" onPress={() => router.push('/schemes/check')} />
      ) : null}

      {g.eligible.length ? <SectionHeader title={t('scheme.status.eligible')} /> : null}
      {g.eligible.map((m) => <SchemeRow key={m.scheme.id} scheme={m.scheme} match={m} />)}
      {g.possibly.length ? <SectionHeader title={t('scheme.status.possibly_eligible')} /> : null}
      {g.possibly.length ? <AppText variant="caption" muted>{t('schemes.possiblyHint')}</AppText> : null}
      {g.possibly.map((m) => <SchemeRow key={m.scheme.id} scheme={m.scheme} match={m} />)}

      {matches.data && g.eligible.length + g.possibly.length === 0 && g.not.length === 0 ? (
        <EmptyState pose="thinking" message={t('schemes.noneYet')} />
      ) : null}
      {g.not.length ? (
        <View style={styles.not}>
          <Button label={showNot ? t('schemes.hideNot') : t('schemes.showNot', { count: g.not.length })} variant="ghost"
            onPress={() => setShowNot((v) => !v)} />
          {showNot ? g.not.map((m) => <SchemeRow key={m.scheme.id} scheme={m.scheme} match={m} />) : null}
        </View>
      ) : null}
      <AppText variant="caption" muted align="center">{t('scheme.disclaimer')}</AppText>
    </Screen>
  );
}

const styles = StyleSheet.create({ not: { gap: space.sm } });
