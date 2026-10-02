/** A past check as a row: verdict pill, score, snippet, source and time. */
import { StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';

import type { FraudCheckItemDTO } from '@/api/endpoints';
import { AppText, Card } from '@/components';
import { relativeTime } from '@/lib/format';
import { radius, space, toneColors } from '@/theme';
import { VERDICT_TONE } from './fraud';

export function FraudRow({ check, right }: { check: FraudCheckItemDTO; right?: React.ReactNode }) {
  const { t } = useTranslation();
  const tone = toneColors[VERDICT_TONE[check.verdict]];
  const [key, count] = relativeTime(check.created_at);
  return (
    <Card onPress={() => router.push({ pathname: '/fraud/result/[id]', params: { id: check.id } })}
      accessibilityLabel={`${t(`verdict.${check.verdict}`)}: ${check.snippet}`} style={styles.row}>
      <View style={[styles.score, { backgroundColor: tone.bg }]}>
        <AppText variant="bodyMedium" tint={tone.fg}>{String(check.risk_score)}</AppText>
      </View>
      <View style={styles.flex}>
        <AppText variant="small" tint={tone.fg}>{t(`verdict.${check.verdict}`)}</AppText>
        <AppText variant="small" numberOfLines={2}>{check.snippet}</AppText>
        <AppText variant="caption" muted>{`${t(`fraud.source.${check.source_app}`)} · ${t(key, { count })}`}</AppText>
      </View>
      {right}
    </Card>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  row: { flexDirection: 'row', alignItems: 'center', gap: space.md },
  score: { width: 48, height: 48, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center' },
});
