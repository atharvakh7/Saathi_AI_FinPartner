/** MetricCard, ProgressRing, RiskGauge, InsightCard, SchemeCard (spec §4.4). Charts are plain SVG. */
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';
import { ChevronRight, CircleAlert, CircleCheck, Info, ShieldAlert } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { color, radius, space, toneColors, type Tone } from '@/theme';
import { AppText } from './AppText';
import { Card, Chip } from './layout';

export function MetricCard({ icon, label, value, subtitle, onPress, tone = 'neutral' }: {
  icon?: ReactNode; label: string; value: string; subtitle?: string; onPress?: () => void; tone?: Tone;
}) {
  return (
    <Card onPress={onPress} accessibilityLabel={`${label}: ${value}`} style={styles.metric}>
      <View style={[styles.metricIcon, { backgroundColor: toneColors[tone].bg }]}>{icon}</View>
      <AppText variant="small" muted numberOfLines={2}>{label}</AppText>
      <AppText variant="h3" numberOfLines={1} adjustsFontSizeToFit>{value}</AppText>
      {subtitle ? <AppText variant="caption" muted numberOfLines={2}>{subtitle}</AppText> : null}
    </Card>
  );
}

/** Percent ring (emergency fund, goals). */
export function ProgressRing({ pct, size = 96, stroke = 10, label, tint = color.primaryLight }: {
  pct: number; size?: number; stroke?: number; label?: string; tint?: string;
}) {
  const clamped = Math.max(0, Math.min(100, pct));
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  return (
    <View style={{ width: size, height: size }} accessible accessibilityRole="progressbar"
      accessibilityValue={{ min: 0, max: 100, now: Math.round(clamped) }} accessibilityLabel={label}>
      <Svg width={size} height={size}>
        <Circle cx={size / 2} cy={size / 2} r={r} stroke={color.primaryTint} strokeWidth={stroke} fill="none" />
        <Circle
          cx={size / 2} cy={size / 2} r={r} stroke={tint} strokeWidth={stroke} fill="none" strokeLinecap="round"
          strokeDasharray={`${c} ${c}`} strokeDashoffset={c * (1 - clamped / 100)}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </Svg>
      <View style={[StyleSheet.absoluteFill, styles.center]}>
        <AppText variant={size >= 96 ? 'h3' : 'small'}>{`${Math.round(clamped)}%`}</AppText>
      </View>
    </View>
  );
}

export type RiskLevel = 'low' | 'medium' | 'high';

const RISK_TONE: Record<RiskLevel, Tone> = { low: 'positive', medium: 'warning', high: 'danger' };

/** Semi-circle gauge 0–5 with low/medium/high bands; level shown as icon + text, not colour alone. */
export function RiskGauge({ score, level, size = 220 }: { score: number; level: RiskLevel; size?: number }) {
  const { t } = useTranslation();
  const stroke = 18;
  const r = (size - stroke) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const point = (v: number) => {
    const a = Math.PI * (1 - Math.max(0, Math.min(5, v)) / 5);
    return [cx + r * Math.cos(a), cy - r * Math.sin(a)] as const;
  };
  const arc = (from: number, to: number) => {
    const [x0, y0] = point(from);
    const [x1, y1] = point(to);
    return `M ${x0} ${y0} A ${r} ${r} 0 0 1 ${x1} ${y1}`;
  };
  const [nx, ny] = point(score);
  const Icon = level === 'low' ? CircleCheck : level === 'medium' ? CircleAlert : ShieldAlert;
  const tone = toneColors[RISK_TONE[level]];
  return (
    <View style={styles.center} accessible accessibilityLabel={`${t('risk.title')}: ${score.toFixed(1)} / 5, ${t(`risk.level.${level}`)}`}>
      <Svg width={size} height={size / 2 + stroke}>
        <Path d={arc(0, 1.66)} stroke={color.success} strokeWidth={stroke} fill="none" />
        <Path d={arc(1.66, 3.33)} stroke={color.warning} strokeWidth={stroke} fill="none" />
        <Path d={arc(3.33, 5)} stroke={color.danger} strokeWidth={stroke} fill="none" />
        <Circle cx={nx} cy={ny} r={stroke / 2 + 4} fill={color.surface} stroke={color.text} strokeWidth={3} />
      </Svg>
      <AppText variant="h1" style={styles.gaugeScore}>{score.toFixed(1)}</AppText>
      <View style={[styles.levelPill, { backgroundColor: tone.bg }]}>
        <Icon color={tone.fg} size={16} />
        <AppText variant="small" tint={tone.fg}>{t(`risk.level.${level}`)}</AppText>
      </View>
    </View>
  );
}

export type InsightTone = 'info' | 'warning' | 'positive';

export function InsightCard({ tone, title, body, ctaLabel, onPress, unread }: {
  tone: InsightTone; title: string; body: string; ctaLabel?: string; onPress?: () => void; unread?: boolean;
}) {
  const c = toneColors[tone];
  const Icon = tone === 'warning' ? CircleAlert : tone === 'positive' ? CircleCheck : Info;
  return (
    <Pressable onPress={onPress} disabled={!onPress} accessibilityRole={onPress ? 'button' : undefined}
      style={[styles.insight, { backgroundColor: c.bg }]}>
      <Icon color={c.fg} size={22} />
      <View style={styles.flex}>
        <View style={styles.rowBetween}>
          <AppText variant="bodyMedium" style={styles.flex}>{title}</AppText>
          {unread ? <View style={styles.dot} accessibilityLabel="unread" /> : null}
        </View>
        <AppText variant="small" muted>{body}</AppText>
        {ctaLabel && onPress ? (
          <View style={styles.cta}>
            <AppText variant="small" tint={c.fg}>{ctaLabel}</AppText>
            <ChevronRight color={c.fg} size={16} />
          </View>
        ) : null}
      </View>
    </Pressable>
  );
}

export type MatchStatus = 'eligible' | 'possibly_eligible' | 'not_eligible';

const MATCH_TONE: Record<MatchStatus, Tone> = { eligible: 'positive', possibly_eligible: 'warning', not_eligible: 'neutral' };

export function SchemeCard({ name, benefit, level, status, needs, onPress }: {
  name: string; benefit: string; level: 'central' | 'state'; status?: MatchStatus | null; needs?: string[]; onPress?: () => void;
}) {
  const { t } = useTranslation();
  return (
    <Card onPress={onPress} accessibilityLabel={name}>
      <View style={styles.rowBetween}>
        <AppText variant="bodyMedium" style={styles.flex}>{name}</AppText>
        <ChevronRight color={color.textMuted} size={18} />
      </View>
      <AppText variant="small" muted numberOfLines={2}>{benefit}</AppText>
      <View style={styles.chips}>
        <Chip label={t(`scheme.level.${level}`)} />
        {status ? (
          <View style={[styles.statusChip, { backgroundColor: toneColors[MATCH_TONE[status]].bg }]}>
            <AppText variant="caption" tint={toneColors[MATCH_TONE[status]].fg}>{t(`scheme.status.${status}`)}</AppText>
          </View>
        ) : null}
      </View>
      {needs && needs.length ? (
        <AppText variant="caption" muted>{needs.join(', ')}</AppText>
      ) : null}
    </Card>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  center: { alignItems: 'center', justifyContent: 'center' },
  rowBetween: { flexDirection: 'row', alignItems: 'center', gap: space.sm },
  metric: { flex: 1, minWidth: 140 },
  metricIcon: { width: 36, height: 36, borderRadius: radius.sm, alignItems: 'center', justifyContent: 'center' },
  gaugeScore: { marginTop: -44 },
  levelPill: { flexDirection: 'row', alignItems: 'center', gap: space.xs, paddingHorizontal: space.md, paddingVertical: space.xs, borderRadius: radius.pill, marginTop: space.sm },
  insight: { flexDirection: 'row', gap: space.md, padding: space.lg, borderRadius: radius.md },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: color.danger },
  cta: { flexDirection: 'row', alignItems: 'center', gap: 2, marginTop: space.xs },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm, marginTop: space.xs },
  statusChip: { paddingHorizontal: space.md, paddingVertical: space.xs, borderRadius: radius.pill, justifyContent: 'center' },
});
