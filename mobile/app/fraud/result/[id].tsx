/**
 * S30 Result (wireframe risk card): big verdict banner (score / 100, verdict, one-line meaning),
 * Saathi's summary, red flags (translated by reason key), what to do, "N others reported this",
 * Report scam, the 1930 helpline for risky messages, the checked text, Delete, Check another.
 */
import { useState } from 'react';
import { Linking, StyleSheet, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { CircleAlert, CircleCheck, Flag, Phone, ShieldAlert, Trash2, Users } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { deleteFraudCheck, getFraudCheck, reportFraudCheck } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import { AppText, Button, Card, ConfirmDialog, EmptyState, ErrorBanner, Screen, SectionHeader, SkeletonCard } from '@/components';
import { fraudKeys, VERDICT_TONE } from '@/features/fraud/fraud';
import { useUiStore } from '@/stores';
import { color, radius, space, toneColors } from '@/theme';

export default function FraudResult() {
  const { t } = useTranslation();
  const { id } = useLocalSearchParams<{ id: string }>();
  const check = useQuery({ queryKey: fraudKeys.check(id), queryFn: () => getFraudCheck(id) });
  const [confirm, setConfirm] = useState(false);
  const report = useMutation({
    mutationFn: () => reportFraudCheck(id),
    onSuccess: () => {
      queryClient.setQueryData(fraudKeys.check(id), (old: typeof check.data) => (old ? { ...old, reported: true } : old));
      useUiStore.getState().showToast(t('fraud.reported'), 'success');
    },
  });
  const remove = useMutation({
    mutationFn: () => deleteFraudCheck(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: fraudKeys.checks });
      setConfirm(false);
      router.back();
    },
  });
  const c = check.data;
  const tone = c ? toneColors[VERDICT_TONE[c.verdict]] : toneColors.neutral;
  const Icon = c?.verdict === 'safe' ? CircleCheck : c?.verdict === 'suspicious' ? CircleAlert : ShieldAlert;

  return (
    <Screen title={t('fraud.resultTitle')} back
      right={c ? <Button label={t('common.delete')} variant="ghost" size="sm" fullWidth={false} icon={<Trash2 color={color.danger} size={18} />} onPress={() => setConfirm(true)} /> : undefined}
      footer={<Button label={t('fraud.checkAnother')} variant="secondary" onPress={() => router.replace('/fraud' as never)} />}>
      {check.isPending ? <SkeletonCard lines={6} /> : null}
      {check.error ? (
        check.error instanceof ApiError && check.error.code === 'NOT_FOUND'
          ? <EmptyState pose="thinking" message={t('errors.NOT_FOUND')} actionLabel={t('common.back')} onAction={() => router.back()} />
          : <ErrorBanner error={check.error} onRetry={() => void check.refetch()} />
      ) : null}
      {c ? (
        <>
          <View style={[styles.banner, { backgroundColor: c.verdict === 'dangerous' ? color.danger : tone.bg }]} accessibilityRole="alert">
            <View style={styles.bannerTop}>
              <Icon color={c.verdict === 'dangerous' ? color.onPrimary : tone.fg} size={28} />
              <AppText variant="small" tint={c.verdict === 'dangerous' ? color.onPrimary : tone.fg}>{t('fraud.riskLevel')}</AppText>
              <AppText variant="h3" tint={c.verdict === 'dangerous' ? color.onPrimary : tone.fg} style={styles.score}>{`${c.risk_score}/100`}</AppText>
            </View>
            <AppText variant="h1" tint={c.verdict === 'dangerous' ? color.onPrimary : tone.fg}>{t(`verdict.${c.verdict}`).toUpperCase()}</AppText>
            <AppText tint={c.verdict === 'dangerous' ? color.onPrimary : tone.fg}>{t(`verdict.subtitle.${c.verdict}`)}</AppText>
          </View>

          <Card>
            <AppText>{c.summary}</AppText>
          </Card>

          {c.reasons.length ? (
            <Card>
              <SectionHeader title={t('fraud.redFlags')} />
              {c.reasons.map((r) => (
                <View key={r.code} style={styles.flag}>
                  <View style={[styles.dot, { backgroundColor: color.danger }]} />
                  <View style={styles.flex}>
                    <AppText variant="bodyMedium">{t(`fraudReason.${r.key}.title`, { defaultValue: r.title })}</AppText>
                    <AppText variant="small" muted>{t(`fraudReason.${r.key}.text`, { defaultValue: r.text })}</AppText>
                  </View>
                </View>
              ))}
            </Card>
          ) : null}

          <View style={[styles.advice, { backgroundColor: toneColors.neutral.bg }]}>
            <AppText variant="small" tint={color.primary}>{t('fraud.whatToDo')}</AppText>
            <AppText variant="bodyMedium" tint={color.primary}>{c.advice}</AppText>
          </View>

          {c.similar_reports_count > 0 ? (
            <View style={styles.row}>
              <Users color={toneColors.warning.fg} size={18} />
              <AppText variant="small" tint={toneColors.warning.fg}>{t('fraud.othersReported', { count: c.similar_reports_count })}</AppText>
            </View>
          ) : null}

          {c.verdict !== 'safe' ? (
            c.reported
              ? <AppText variant="small" tint={color.success} align="center">{t('fraud.reported')}</AppText>
              : <Button label={t('fraud.report')} variant="danger" loading={report.isPending} icon={<Flag color={color.onPrimary} size={18} />} onPress={() => report.mutate()} />
          ) : null}
          {report.error ? <ErrorBanner error={report.error} /> : null}
          {c.verdict !== 'safe' ? (
            <Card style={styles.row}>
              <Phone color={color.danger} size={20} />
              <View style={styles.flex}>
                <AppText variant="small">{t('verdict.helpline')}</AppText>
                <Button label={t('fraud.call1930')} variant="ghost" size="sm" fullWidth={false} onPress={() => void Linking.openURL('tel:1930')} />
              </View>
            </Card>
          ) : null}

          <Card>
            <AppText variant="caption" muted>{t('fraud.youChecked', { source: t(`fraud.source.${c.source_app}`) })}</AppText>
            <AppText variant="small" numberOfLines={6}>{c.snippet}</AppText>
          </Card>
        </>
      ) : null}
      <ConfirmDialog visible={confirm} title={t('fraud.deleteTitle')} message={t('fraud.deleteMessage')} confirmLabel={t('common.delete')}
        danger loading={remove.isPending} onConfirm={() => remove.mutate()} onCancel={() => setConfirm(false)}>
        {remove.error ? <ErrorBanner error={remove.error} /> : null}
      </ConfirmDialog>
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  row: { flexDirection: 'row', alignItems: 'center', gap: space.sm },
  banner: { padding: space.xl, borderRadius: radius.lg, gap: space.xs },
  bannerTop: { flexDirection: 'row', alignItems: 'center', gap: space.sm },
  score: { marginLeft: 'auto' },
  flag: { flexDirection: 'row', gap: space.md, alignItems: 'flex-start', paddingVertical: space.xs },
  dot: { width: 8, height: 8, borderRadius: 4, marginTop: 8 },
  advice: { padding: space.lg, borderRadius: radius.md, gap: space.xs },
});
