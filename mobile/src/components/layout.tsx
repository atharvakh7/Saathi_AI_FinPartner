/** Screen, Card, Chip, SegmentedTabs, StepList (spec §4.4). */
import type { ReactNode } from 'react';
import { Pressable, ScrollView, StyleSheet, View, type ViewStyle } from 'react-native';
import { router } from 'expo-router';
import { ChevronLeft } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';
import { SafeAreaView } from 'react-native-safe-area-context';

import { color, MAX_CONTENT_WIDTH, MIN_TOUCH, radius, SCREEN_PADDING, shadow, space } from '@/theme';
import { AppText } from './AppText';
import { OfflineBanner } from './feedback';

export interface ScreenProps {
  title?: string;
  back?: boolean | (() => void);
  right?: ReactNode;
  scroll?: boolean;
  children: ReactNode;
  footer?: ReactNode;
  padded?: boolean;
  refreshControl?: React.ComponentProps<typeof ScrollView>['refreshControl'];
}

/** Safe-area wrapper with optional header, scroll, sticky footer, and the offline banner. */
export function Screen({ title, back, right, scroll = true, children, footer, padded = true, refreshControl }: ScreenProps) {
  const { t } = useTranslation();
  const onBack = typeof back === 'function' ? back : () => (router.canGoBack() ? router.back() : router.replace('/'));
  const body = (
    <View style={[styles.content, padded && styles.padded]}>{children}</View>
  );
  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
      <OfflineBanner />
      {(title || back || right) && (
        <View style={styles.header}>
          {back ? (
            <Pressable onPress={onBack} accessibilityRole="button" accessibilityLabel={t('common.back')} style={styles.iconBtn} hitSlop={8}>
              <ChevronLeft color={color.text} size={26} />
            </Pressable>
          ) : (
            <View style={styles.iconBtn} />
          )}
          <AppText variant="h3" numberOfLines={1} style={styles.title} accessibilityRole="header">
            {title ?? ''}
          </AppText>
          <View style={styles.headerRight}>{right}</View>
        </View>
      )}
      {scroll ? (
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled" refreshControl={refreshControl}>
          {body}
        </ScrollView>
      ) : (
        <View style={styles.flex}>{body}</View>
      )}
      {footer ? <View style={styles.footer}>{footer}</View> : null}
    </SafeAreaView>
  );
}

export function Card({ children, style, onPress, accessibilityLabel }: {
  children: ReactNode; style?: ViewStyle; onPress?: () => void; accessibilityLabel?: string;
}) {
  if (onPress) {
    return (
      <Pressable onPress={onPress} accessibilityRole="button" accessibilityLabel={accessibilityLabel}
        style={({ pressed }) => [styles.card, pressed && styles.pressed, style]}>
        {children}
      </Pressable>
    );
  }
  return <View style={[styles.card, style]}>{children}</View>;
}

export function Chip({ label, selected, onPress, icon }: {
  label: string; selected?: boolean; onPress?: () => void; icon?: ReactNode;
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={!onPress}
      accessibilityRole={onPress ? 'button' : 'text'}
      accessibilityState={{ selected: !!selected }}
      style={[styles.chip, selected && styles.chipOn]}
    >
      {icon}
      <AppText variant="small" tint={selected ? color.onPrimary : color.primary}>{label}</AppText>
    </Pressable>
  );
}

export function SegmentedTabs<T extends string>({ options, value, onChange }: {
  options: { value: T; label: string }[]; value: T; onChange: (v: T) => void;
}) {
  return (
    <View style={styles.segments} accessibilityRole="tablist">
      {options.map((o) => {
        const on = o.value === value;
        return (
          <Pressable key={o.value} onPress={() => onChange(o.value)} accessibilityRole="tab"
            accessibilityState={{ selected: on }} style={[styles.segment, on && styles.segmentOn]}>
            <AppText variant="small" tint={on ? color.onPrimary : color.textMuted} numberOfLines={1}>{o.label}</AppText>
          </Pressable>
        );
      })}
    </View>
  );
}

export function StepList({ steps }: { steps: { title: string; description?: string }[] }) {
  return (
    <View style={{ gap: space.lg }}>
      {steps.map((s, i) => (
        <View key={i} style={styles.step}>
          <View style={styles.stepNo}>
            <AppText variant="small" tint={color.onPrimary}>{String(i + 1)}</AppText>
          </View>
          <View style={styles.flex}>
            <AppText variant="bodyMedium">{s.title}</AppText>
            {s.description ? <AppText variant="small" muted>{s.description}</AppText> : null}
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: color.bg },
  flex: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: space.sm, minHeight: 56 },
  iconBtn: { width: MIN_TOUCH, height: MIN_TOUCH, alignItems: 'center', justifyContent: 'center' },
  title: { flex: 1, textAlign: 'center' },
  headerRight: { minWidth: MIN_TOUCH, alignItems: 'flex-end', paddingRight: space.sm },
  scroll: { flexGrow: 1 },
  content: { flexGrow: 1, width: '100%', maxWidth: MAX_CONTENT_WIDTH, alignSelf: 'center', gap: space.lg },
  padded: { paddingHorizontal: SCREEN_PADDING, paddingVertical: space.lg },
  footer: {
    paddingHorizontal: SCREEN_PADDING, paddingVertical: space.md, borderTopWidth: 1, borderTopColor: color.border,
    backgroundColor: color.surface, width: '100%', maxWidth: MAX_CONTENT_WIDTH, alignSelf: 'center',
  },
  card: {
    backgroundColor: color.surface, borderRadius: radius.md, borderWidth: 1, borderColor: color.border,
    padding: space.lg, gap: space.sm, ...shadow,
  },
  pressed: { opacity: 0.9 },
  chip: {
    flexDirection: 'row', alignItems: 'center', gap: space.xs, minHeight: 36, paddingHorizontal: space.md,
    borderRadius: radius.pill, borderWidth: 1, borderColor: color.primary, backgroundColor: color.surface,
  },
  chipOn: { backgroundColor: color.primary },
  segments: { flexDirection: 'row', backgroundColor: color.primaryTint, borderRadius: radius.pill, padding: space.xs },
  segment: { flex: 1, minHeight: 40, alignItems: 'center', justifyContent: 'center', borderRadius: radius.pill, paddingHorizontal: space.sm },
  segmentOn: { backgroundColor: color.primary },
  step: { flexDirection: 'row', gap: space.md },
  stepNo: {
    width: 28, height: 28, borderRadius: 14, backgroundColor: color.primary, alignItems: 'center', justifyContent: 'center', marginTop: 2,
  },
});
