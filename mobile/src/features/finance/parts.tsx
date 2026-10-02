/** Pieces shared by Home and the finance screens: transaction row, month switcher. */
import { Pressable, StyleSheet, View } from 'react-native';
import { ChevronLeft, ChevronRight } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import type { TransactionDTO } from '@/api/endpoints';
import { AppText } from '@/components';
import { apiMonth, displayMonth, inr, shiftMonth } from '@/lib/format';
import { color, MIN_TOUCH, radius, space } from '@/theme';
import { CategoryIcon } from './categories';

export function TransactionRow({ tx, onPress }: { tx: TransactionDTO; onPress?: () => void }) {
  const { t } = useTranslation();
  const income = tx.type === 'income';
  const amount = `${income ? '+' : '−'}${inr(tx.amount_inr)}`;
  const title = t(`txcat.${tx.category}`);
  return (
    <Pressable onPress={onPress} disabled={!onPress} accessibilityRole="button"
      accessibilityLabel={`${title}, ${amount}${tx.note ? `, ${tx.note}` : ''}`}
      style={({ pressed }) => [styles.row, pressed && styles.pressed]}>
      <CategoryIcon category={tx.category} type={tx.type} />
      <View style={styles.flex}>
        <AppText variant="bodyMedium" numberOfLines={1}>{title}</AppText>
        {tx.note ? <AppText variant="small" muted numberOfLines={1}>{tx.note}</AppText> : null}
      </View>
      <AppText variant="bodyMedium" tint={income ? color.success : color.text}>{amount}</AppText>
    </Pressable>
  );
}

/** "‹ Sep 2026 ›" — no months after the current one. */
export function MonthSwitcher({ month, onChange }: { month: string; onChange: (m: string) => void }) {
  const { t } = useTranslation();
  const atCurrent = month >= apiMonth();
  return (
    <View style={styles.month}>
      <Pressable onPress={() => onChange(shiftMonth(month, -1))} accessibilityRole="button"
        accessibilityLabel={t('date.prevMonth')} hitSlop={8} style={styles.navBtn}>
        <ChevronLeft color={color.text} size={22} />
      </Pressable>
      <AppText variant="h3" align="center" style={styles.flex} accessibilityLiveRegion="polite">{displayMonth(month)}</AppText>
      <Pressable onPress={() => onChange(shiftMonth(month, 1))} disabled={atCurrent} accessibilityRole="button"
        accessibilityLabel={t('date.nextMonth')} accessibilityState={{ disabled: atCurrent }} hitSlop={8} style={styles.navBtn}>
        <ChevronRight color={atCurrent ? color.border : color.text} size={22} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  row: {
    flexDirection: 'row', alignItems: 'center', gap: space.md, minHeight: MIN_TOUCH + 16, paddingVertical: space.sm,
    paddingHorizontal: space.lg, marginBottom: space.sm, borderRadius: radius.md, backgroundColor: color.surface,
  },
  pressed: { opacity: 0.7 },
  month: { flexDirection: 'row', alignItems: 'center' },
  navBtn: { width: MIN_TOUCH, height: MIN_TOUCH, alignItems: 'center', justifyContent: 'center' },
});
