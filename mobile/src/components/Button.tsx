/** Button (spec §4.4): primary / secondary / ghost / danger; inline spinner while loading. */
import type { ReactNode } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, View, type ViewStyle } from 'react-native';

import { color, MIN_TOUCH, radius, space } from '@/theme';
import { AppText } from './AppText';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

export interface ButtonProps {
  label: string;
  onPress?: () => void;
  variant?: ButtonVariant;
  loading?: boolean;
  disabled?: boolean;
  icon?: ReactNode;
  fullWidth?: boolean;
  size?: 'md' | 'sm';
  style?: ViewStyle;
  accessibilityLabel?: string;
  testID?: string;
}

const VARIANTS: Record<ButtonVariant, { bg: string; fg: string; border: string }> = {
  primary: { bg: color.primary, fg: color.onPrimary, border: color.primary },
  secondary: { bg: color.primaryTint, fg: color.primary, border: color.primaryTint },
  ghost: { bg: 'transparent', fg: color.primary, border: 'transparent' },
  danger: { bg: color.danger, fg: color.onPrimary, border: color.danger },
};

export function Button({
  label, onPress, variant = 'primary', loading, disabled, icon, fullWidth = true, size = 'md', style,
  accessibilityLabel, testID,
}: ButtonProps) {
  const v = VARIANTS[variant];
  const inactive = disabled || loading;
  return (
    <Pressable
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityState={{ disabled: !!inactive, busy: !!loading }}
      disabled={inactive}
      onPress={onPress}
      style={({ pressed }) => [
        styles.base,
        size === 'sm' && styles.sm,
        { backgroundColor: v.bg, borderColor: v.border },
        fullWidth && styles.full,
        inactive && styles.inactive,
        pressed && !inactive && styles.pressed,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={v.fg} />
      ) : (
        <View style={styles.row}>
          {icon}
          <AppText variant={size === 'sm' ? 'small' : 'bodyMedium'} tint={v.fg} numberOfLines={2} align="center">
            {label}
          </AppText>
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: MIN_TOUCH + 4,
    paddingHorizontal: space.xl,
    paddingVertical: space.md,
    borderRadius: radius.pill,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sm: { minHeight: 40, paddingVertical: space.sm, paddingHorizontal: space.lg },
  full: { alignSelf: 'stretch' },
  row: { flexDirection: 'row', alignItems: 'center', gap: space.sm },
  inactive: { opacity: 0.5 },
  pressed: { opacity: 0.85, transform: [{ scale: 0.99 }] },
});
