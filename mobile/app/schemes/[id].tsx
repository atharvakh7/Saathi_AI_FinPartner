/**
 * S27 Scheme detail: name, level / state, your match (each rule: met / not met / not known yet, with
 * "Answer questions" when something is unknown), benefit, about, how to apply (steps), documents
 * checklist (required / optional), official website, Save / I've applied / Not for me, last verified
 * date and the disclaimer. Machine translations carry "Simplified by AI".
 */
import { Linking, StyleSheet, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Bookmark, CircleCheck, CircleHelp, CircleX, ExternalLink, FileText, Sparkles } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { getScheme, setSchemeTracking, type TrackingStatus } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import { AppText, Button, Card, Chip, EmptyState, ErrorBanner, Screen, SectionHeader, SkeletonCard, StepList } from '@/components';
import { schemeKeys } from '@/features/schemes/schemes';
import { displayDate } from '@/lib/format';
import { useUiStore } from '@/stores';
import { useLanguageStore } from '@/stores/language';
import { color, radius, space, toneColors, type Tone } from '@/theme';

const STATUS_TONE = { eligible: 'positive', possibly_eligible: 'warning', not_eligible: 'neutral' } as const satisfies Record<string, Tone>;

export default function SchemeDetail() {
  const { t } = useTranslation();
  const { id } = useLocalSearchParams<{ id: string }>();
  const language = useLanguageStore((s) => s.language);
  const key = schemeKeys.detail(id, language);
  const detail = useQuery({ queryKey: key, queryFn: () => getScheme(id) });
  const track = useMutation({
    mutationFn: (status: TrackingStatus | null) => setSchemeTracking(id, status),
    onSuccess: (_d, status) => {
      queryClient.setQueryData(key, (old: typeof detail.data) => (old ? { ...old, tracking_status: status } : old));
      useUiStore.getState().showToast(t(status ? `schemes.track.${status}Done` : 'schemes.track.cleared'), 'success');
    },
  });
  const d = detail.data;
  const s = d?.scheme;
  const toggle = (status: TrackingStatus) => track.mutate(d?.tracking_status === status ? null : status);

  return (
    <Screen title={t('schemes.detailTitle')} back>
      {detail.isPending ? <><SkeletonCard lines={4} /><AppText variant="caption" muted align="center">{t('schemes.loadingDetail')}</AppText></> : null}
      {detail.error ? (
        detail.error instanceof ApiError && detail.error.code === 'NOT_FOUND'
          ? <EmptyState pose="thinking" message={t('errors.NOT_FOUND')} actionLabel={t('common.back')} onAction={() => router.back()} />
          : <ErrorBanner error={detail.error} onRetry={() => void detail.refetch()} />
      ) : null}
      {d && s ? (
        <>
          <Card>
            <AppText variant="h2">{s.name}</AppText>
            <View style={styles.chips}>
              <Chip label={s.level === 'state' && s.state_code ? `${t('scheme.level.state')} · ${t(`state.${s.state_code}`)}` : t(`scheme.level.${s.level}`)} />
              <Chip label={t(`category.${s.category_slug}`)} />
            </View>
            {s.ministry_or_dept ? <AppText variant="caption" muted>{s.ministry_or_dept}</AppText> : null}
            <View style={[styles.benefit, { backgroundColor: toneColors.positive.bg }]}>
              <AppText variant="small" tint={toneColors.positive.fg}>{t('schemes.benefit')}</AppText>
              <AppText variant="bodyMedium">{s.benefit_summary}</AppText>
            </View>
            {s.deadline_on ? <AppText variant="small" tint={toneColors.warning.fg}>{t('schemes.deadline', { date: displayDate(s.deadline_on) })}</AppText> : null}
            {s.translation_source === 'llm' ? (
              <View style={styles.ai}><Sparkles color={toneColors.info.fg} size={14} /><AppText variant="caption" tint={toneColors.info.fg}>{t('learn.simplifiedByAi')}</AppText></View>
            ) : null}
          </Card>

          <Card>
            <View style={styles.row}>
              <AppText variant="bodyMedium" style={styles.flex}>{t('schemes.yourMatch')}</AppText>
              <View style={[styles.pill, { backgroundColor: toneColors[STATUS_TONE[d.match.status]].bg }]}>
                <AppText variant="caption" tint={toneColors[STATUS_TONE[d.match.status]].fg}>{t(`scheme.status.${d.match.status}`)}</AppText>
              </View>
            </View>
            {d.match.rules.map((r) => {
              const Icon = r.result === 'pass' ? CircleCheck : r.result === 'fail' ? CircleX : CircleHelp;
              const tint = r.result === 'pass' ? color.success : r.result === 'fail' ? color.danger : toneColors.warning.fg;
              return (
                <View key={r.rule_key} style={styles.rule}>
                  <Icon color={tint} size={18} />
                  <AppText variant="small" style={styles.flex}>{r.explanation}</AppText>
                </View>
              );
            })}
            {d.match.rules.some((r) => r.result === 'unknown') ? (
              <Button label={t('schemes.answerMore')} variant="secondary" size="sm" onPress={() => router.push('/schemes/check')} />
            ) : null}
          </Card>

          {s.description ? (
            <Card>
              <SectionHeader title={t('schemes.about')} />
              <AppText>{s.description}</AppText>
            </Card>
          ) : null}

          {d.steps.length ? (
            <Card>
              <SectionHeader title={t('schemes.howToApply')} />
              {s.application_mode ? <AppText variant="caption" muted>{s.application_mode}</AppText> : null}
              <StepList steps={d.steps.map((st) => ({ title: st.title, description: st.description }))} />
            </Card>
          ) : null}

          {d.documents.length ? (
            <Card>
              <SectionHeader title={t('schemes.documents')} />
              {d.documents.map((doc, i) => (
                <View key={i} style={styles.rule}>
                  <FileText color={color.primary} size={18} />
                  <AppText variant="small" style={styles.flex}>{doc.name}</AppText>
                  <AppText variant="caption" tint={doc.is_mandatory ? color.danger : color.textMuted}>
                    {doc.is_mandatory ? t('common.required') : t('common.optional')}
                  </AppText>
                </View>
              ))}
            </Card>
          ) : null}

          <Button label={t('schemes.official')} icon={<ExternalLink color={color.onPrimary} size={18} />}
            onPress={() => void Linking.openURL(s.official_url)} />
          <View style={styles.track}>
            {(['saved', 'applied', 'dismissed'] as const).map((st) => (
              <Chip key={st} label={t(`schemes.track.${st}`)} selected={d.tracking_status === st} onPress={() => toggle(st)}
                icon={st === 'saved' ? <Bookmark color={d.tracking_status === st ? color.onPrimary : color.primary} size={14} /> : undefined} />
            ))}
          </View>
          {track.error ? <ErrorBanner error={track.error} /> : null}
          <AppText variant="caption" muted align="center">
            {`${t('schemes.verified', { date: displayDate(s.last_verified_on) })} · ${d.disclaimer}`}
          </AppText>
        </>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  row: { flexDirection: 'row', alignItems: 'center', gap: space.sm },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
  benefit: { padding: space.md, borderRadius: radius.md, gap: 2 },
  ai: { flexDirection: 'row', alignItems: 'center', gap: space.xs },
  pill: { paddingHorizontal: space.md, paddingVertical: space.xs, borderRadius: radius.pill },
  rule: { flexDirection: 'row', alignItems: 'flex-start', gap: space.sm, paddingVertical: 2 },
  track: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm, justifyContent: 'center' },
});
