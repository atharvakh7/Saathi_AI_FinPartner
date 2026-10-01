/** A tappable settings row (icon, label, optional value) and a toggle row. */
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Switch, View } from 'react-native';
import { ChevronRight } from 'lucide-react-native';

import { AppText } from '@/components';
import { color, MIN_TOUCH, space } from '@/theme';

export function SettingsRow({ icon, label, value, onPress, danger }: {
  icon?: ReactNode; label: string; value?: string; onPress?: () => void; danger?: boolean;
}) {
  return (
    <Pressable onPress={onPress} disabled={!onPress} accessibilityRole="button" accessibilityLabel={label}
      style={({ pressed }) => [styles.row, pressed && styles.pressed]}>
      {icon ? <View style={styles.icon}>{icon}</View> : null}
      <AppText style={styles.flex} tint={danger ? color.danger : color.text}>{label}</AppText>
      {value ? <AppText variant="small" muted numberOfLines={1}>{value}</AppText> : null}
      {onPress ? <ChevronRight color={color.textMuted} size={18} /> : null}
    </Pressable>
  );
}

export function ToggleRow({ label, hint, value, onChange, disabled }: {
  label: string; hint?: string; value: boolean; onChange: (v: boolean) => void; disabled?: boolean;
}) {
  return (
    <View style={styles.row}>
      <View style={styles.flex}>
        <AppText>{label}</AppText>
        {hint ? <AppText variant="caption" muted>{hint}</AppText> : null}
      </View>
      <Switch
        value={value}
        onValueChange={onChange}
        disabled={disabled}
        accessibilityLabel={label}
        trackColor={{ true: color.primaryLight, false: color.border }}
        thumbColor={color.surface}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  row: { flexDirection: 'row', alignItems: 'center', gap: space.md, minHeight: MIN_TOUCH + 8, paddingVertical: space.sm },
  icon: { width: 28, alignItems: 'center' },
  pressed: { opacity: 0.7 },
});
