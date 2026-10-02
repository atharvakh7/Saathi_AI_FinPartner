/**
 * Date input: shows "30 Sep 2026", opens a month calendar in a bottom sheet (no date-picker library,
 * same approach as Select). `min`/`max` (YYYY-MM-DD) disable days outside the range; `quick` adds
 * Today / Yesterday chips for money entries (S15).
 */
import { useState } from 'react';
import { Modal, Pressable, StyleSheet, View } from 'react-native';
import { CalendarDays, ChevronLeft, ChevronRight } from 'lucide-react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { apiDate, displayDate, displayMonth, monthGrid, parseApiDate, shiftMonth } from '@/lib/format';
import { color, MIN_TOUCH, radius, space } from '@/theme';
import { AppText } from './AppText';
import { Chip } from './layout';

export function DateField({ label, value, onChange, min, max, error, quick }: {
  label?: string; value: string; onChange: (v: string) => void; min?: string; max?: string;
  error?: string | null; quick?: boolean;
}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [view, setView] = useState(value.slice(0, 7));
  const now = new Date();
  const today = apiDate(now);
  const yesterday = apiDate(new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1));
  const weekdays = t('date.weekdays').split(',');
  const allowed = (d: string) => (!min || d >= min) && (!max || d <= max);
  const prevOff = !!min && shiftMonth(view, -1) < min.slice(0, 7);
  const nextOff = !!max && shiftMonth(view, 1) > max.slice(0, 7);
  const show = () => {
    setView(value.slice(0, 7));
    setOpen(true);
  };

  return (
    <View style={styles.field}>
      {label ? <AppText variant="small">{label}</AppText> : null}
      <Pressable onPress={show} accessibilityRole="button" accessibilityLabel={label}
        accessibilityValue={{ text: displayDate(value) }} style={[styles.input, !!error && styles.errored]}>
        <AppText style={styles.flex}>{displayDate(value)}</AppText>
        <CalendarDays color={color.textMuted} size={20} />
      </Pressable>
      {quick ? (
        <View style={styles.chips}>
          {allowed(today) ? <Chip label={t('common.today')} selected={value === today} onPress={() => onChange(today)} /> : null}
          {allowed(yesterday) ? (
            <Chip label={t('common.yesterday')} selected={value === yesterday} onPress={() => onChange(yesterday)} />
          ) : null}
          <Chip label={t('date.other')} selected={value !== today && value !== yesterday} onPress={show} />
        </View>
      ) : null}
      {error ? <AppText variant="caption" tint={color.danger}>{error}</AppText> : null}

      <Modal visible={open} transparent animationType="slide" onRequestClose={() => setOpen(false)}>
        <Pressable style={styles.backdrop} onPress={() => setOpen(false)} accessibilityLabel={t('common.close')} />
        <SafeAreaView edges={['bottom']} style={styles.sheet}>
          <View style={styles.grabber} />
          <View style={styles.monthRow}>
            <Pressable onPress={() => setView((v) => shiftMonth(v, -1))} hitSlop={8} accessibilityRole="button"
              accessibilityLabel={t('date.prevMonth')} disabled={prevOff} style={styles.navBtn}>
              <ChevronLeft color={prevOff ? color.border : color.text} size={24} />
            </Pressable>
            <AppText variant="h3" style={styles.flex} align="center">{displayMonth(view)}</AppText>
            <Pressable onPress={() => setView((v) => shiftMonth(v, 1))} hitSlop={8} accessibilityRole="button"
              accessibilityLabel={t('date.nextMonth')} disabled={nextOff} style={styles.navBtn}>
              <ChevronRight color={nextOff ? color.border : color.text} size={24} />
            </Pressable>
          </View>
          <View style={styles.week}>
            {weekdays.map((w, i) => (
              <AppText key={i} variant="caption" muted align="center" style={styles.cell}>{w}</AppText>
            ))}
          </View>
          {monthGrid(view).map((row, r) => (
            <View key={r} style={styles.week}>
              {row.map((d, i) => {
                if (!d) return <View key={i} style={styles.cell} />;
                const on = d === value;
                const ok = allowed(d);
                return (
                  <Pressable key={i} disabled={!ok} onPress={() => { onChange(d); setOpen(false); }}
                    accessibilityRole="button" accessibilityLabel={displayDate(d)}
                    accessibilityState={{ selected: on, disabled: !ok }} style={styles.cell}>
                    <View style={[styles.day, on && styles.dayOn, d === today && !on && styles.dayToday]}>
                      <AppText tint={on ? color.onPrimary : ok ? color.text : color.border}>
                        {String(parseApiDate(d).getDate())}
                      </AppText>
                    </View>
                  </Pressable>
                );
              })}
            </View>
          ))}
        </SafeAreaView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  field: { gap: space.xs, minWidth: 0 },
  input: {
    flexDirection: 'row', alignItems: 'center', gap: space.sm, minHeight: MIN_TOUCH + 4, paddingHorizontal: space.lg,
    borderWidth: 1.5, borderColor: 'transparent', borderRadius: radius.md, backgroundColor: color.fill,
  },
  errored: { borderColor: color.danger },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm, marginTop: space.xs },
  backdrop: { flex: 1, backgroundColor: 'rgba(20,35,43,0.4)' },
  sheet: {
    backgroundColor: color.surface, borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg,
    paddingHorizontal: space.lg, paddingBottom: space.xl,
  },
  grabber: { alignSelf: 'center', width: 40, height: 4, borderRadius: 2, backgroundColor: color.border, marginVertical: space.md },
  monthRow: { flexDirection: 'row', alignItems: 'center', marginBottom: space.sm },
  navBtn: { width: MIN_TOUCH, height: MIN_TOUCH, alignItems: 'center', justifyContent: 'center' },
  week: { flexDirection: 'row' },
  cell: { flex: 1, alignItems: 'center', justifyContent: 'center', minHeight: MIN_TOUCH },
  day: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  dayOn: { backgroundColor: color.primary },
  dayToday: { borderWidth: 1.5, borderColor: color.primary },
});
