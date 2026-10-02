/**
 * Wireframe building blocks: Logo (teal "S" mark + wordmark), GradientBackground, PageHeader
 * (title / subtitle with the mascot on the right), SectionHeader ("Quick Summary · View All"),
 * IconBadge (rounded-square tinted icon), ProgressBar.
 */
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, View, type ViewStyle } from 'react-native';
import Svg, { Defs, LinearGradient, Rect, Stop } from 'react-native-svg';
import { useTranslation } from 'react-i18next';

import { color, radius, space, toneColors, type Tone } from '@/theme';
import { AppText } from './AppText';
import { Mascot, type MascotPose } from './Mascot';

export function Logo({ size = 56, wordmark = true }: { size?: number; wordmark?: boolean }) {
  const { t } = useTranslation();
  return (
    <View style={styles.logo} accessible accessibilityRole="image" accessibilityLabel={t('common.appName')}>
      <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
        <View style={[styles.logoDot, { width: size * 0.2, height: size * 0.2, borderRadius: size * 0.1, top: size * 0.02, left: size * 0.16 }]} />
        <AppText textLanguage="en" style={{ fontSize: size, lineHeight: size * 1.1, color: color.primaryLight }}>S</AppText>
      </View>
      {wordmark ? <AppText variant="h1" textLanguage="en" tint={color.primary}>{t('common.appName')}</AppText> : null}
    </View>
  );
}

/** Soft white -> teal tint wash, absolutely filling its parent. */
export function GradientBackground() {
  return (
    <Svg style={StyleSheet.absoluteFill} preserveAspectRatio="none" width="100%" height="100%">
      <Defs>
        <LinearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor={color.surface} />
          <Stop offset="1" stopColor={color.primaryTint} />
        </LinearGradient>
      </Defs>
      <Rect x="0" y="0" width="100%" height="100%" fill="url(#bg)" />
    </Svg>
  );
}

export function PageHeader({ title, subtitle, pose = 'wave', right, mascotSize = 60 }: {
  title: string; subtitle?: string; pose?: MascotPose | null; right?: ReactNode; mascotSize?: number;
}) {
  return (
    <View style={styles.header}>
      <View style={styles.flex}>
        <AppText variant="h2" accessibilityRole="header">{title}</AppText>
        {subtitle ? <AppText variant="small" muted>{subtitle}</AppText> : null}
      </View>
      {right}
      {pose ? <Mascot pose={pose} size={mascotSize} variant="avatar" /> : null}
    </View>
  );
}

export function SectionHeader({ title, action, onAction }: { title: string; action?: string; onAction?: () => void }) {
  return (
    <View style={styles.section}>
      <AppText variant="bodyMedium" style={styles.flex}>{title}</AppText>
      {action && onAction ? (
        <Pressable onPress={onAction} hitSlop={10} accessibilityRole="link">
          <AppText variant="small" tint={color.primaryLight}>{action}</AppText>
        </Pressable>
      ) : null}
    </View>
  );
}

export function IconBadge({ children, tone = 'neutral', size = 40, style }: {
  children: ReactNode; tone?: Tone; size?: number; style?: ViewStyle;
}) {
  return (
    <View style={[styles.badge, { width: size, height: size, borderRadius: size * 0.3, backgroundColor: toneColors[tone].bg }, style]}>
      {children}
    </View>
  );
}

export function ProgressBar({ pct, tint = color.success, height = 6 }: { pct: number; tint?: string; height?: number }) {
  const clamped = Math.max(0, Math.min(100, pct));
  return (
    <View style={[styles.track, { height, borderRadius: height / 2 }]} accessible accessibilityRole="progressbar"
      accessibilityValue={{ min: 0, max: 100, now: Math.round(clamped) }}>
      <View style={{ width: `${clamped}%`, height, borderRadius: height / 2, backgroundColor: tint }} />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  logo: { alignItems: 'center', gap: 0 },
  logoDot: { position: 'absolute', backgroundColor: color.primary },
  header: { flexDirection: 'row', alignItems: 'center', gap: space.sm },
  section: { flexDirection: 'row', alignItems: 'center', gap: space.sm },
  badge: { alignItems: 'center', justifyContent: 'center' },
  track: { backgroundColor: color.primaryTint, overflow: 'hidden', alignSelf: 'stretch' },
});
