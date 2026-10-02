/** TextField, AmountInput, Select, LanguageOption (spec §4.4). */
import { forwardRef, useState, type ReactNode } from 'react';
import { FlatList, Modal, Pressable, StyleSheet, TextInput, View, type TextInputProps } from 'react-native';
import { Check, ChevronDown } from 'lucide-react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import type { Language } from '@/i18n';
import { groupIndian, parseAmount } from '@/lib/format';
import { useLanguageStore } from '@/stores/language';
import { color, fontFor, MAX_FONT_SCALE, MIN_TOUCH, radius, shadow, space } from '@/theme';
import { AppText } from './AppText';

export interface TextFieldProps extends Omit<TextInputProps, 'style'> {
  label?: string;
  helper?: string;
  error?: string | null;
  prefix?: ReactNode;
  suffix?: ReactNode;
}

export const TextField = forwardRef<TextInput, TextFieldProps>(function TextField(
  { label, helper, error, prefix, suffix, editable = true, ...rest }, ref,
) {
  const language = useLanguageStore((s) => s.language);
  const [focused, setFocused] = useState(false);
  return (
    <View style={styles.field}>
      {label ? <AppText variant="small" style={styles.label}>{label}</AppText> : null}
      <View style={[styles.inputRow, focused && styles.focused, !!error && styles.errored, !editable && styles.disabled]}>
        {typeof prefix === 'string' ? <AppText muted>{prefix}</AppText> : prefix}
        <TextInput
          ref={ref}
          editable={editable}
          placeholderTextColor={color.textMuted}
          maxFontSizeMultiplier={MAX_FONT_SCALE}
          accessibilityLabel={label}
          accessibilityHint={error ?? helper}
          style={[styles.input, { fontFamily: fontFor(language, 'body') }]}
          onFocus={(e) => { setFocused(true); rest.onFocus?.(e); }}
          onBlur={(e) => { setFocused(false); rest.onBlur?.(e); }}
          {...rest}
        />
        {suffix}
      </View>
      {error ? <AppText variant="caption" tint={color.danger}>{error}</AppText>
        : helper ? <AppText variant="caption" muted>{helper}</AppText> : null}
    </View>
  );
});

/** ₹ input that shows Indian grouping while typing and reports a number (or null). */
export function AmountInput({ value, onChange, ...rest }: Omit<TextFieldProps, 'value' | 'onChangeText' | 'onChange'> & {
  value: number | null; onChange: (v: number | null) => void;
}) {
  const [text, setText] = useState(value === null ? '' : groupIndian(value));
  return (
    <TextField
      {...rest}
      prefix="₹"
      keyboardType="decimal-pad"
      value={text}
      onChangeText={(raw) => {
        const cleaned = raw.replace(/[^\d.]/g, '').replace(/(\..*)\./g, '$1');
        const [whole = '', frac] = cleaned.split('.');
        const grouped = whole ? groupIndian(Number(whole), 0) : '';
        setText(frac !== undefined ? `${grouped}.${frac.slice(0, 2)}` : grouped);
        onChange(parseAmount(cleaned));
      }}
    />
  );
}

export interface SelectOption<T extends string> {
  value: T;
  label: string;
  hint?: string;
}

/** Single select in a bottom sheet (no search, spec §4.4). */
export function Select<T extends string>({ label, value, options, onChange, placeholder, error }: {
  label?: string; value: T | null; options: SelectOption<T>[]; onChange: (v: T) => void; placeholder?: string; error?: string | null;
}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const selected = options.find((o) => o.value === value);
  return (
    <View style={styles.field}>
      {label ? <AppText variant="small" style={styles.label}>{label}</AppText> : null}
      <Pressable
        onPress={() => setOpen(true)}
        accessibilityRole="button"
        accessibilityLabel={label}
        accessibilityValue={{ text: selected?.label ?? placeholder ?? '' }}
        style={[styles.inputRow, !!error && styles.errored]}
      >
        <AppText style={styles.flex} muted={!selected} numberOfLines={1}>{selected?.label ?? placeholder ?? ''}</AppText>
        <ChevronDown color={color.textMuted} size={20} />
      </Pressable>
      {error ? <AppText variant="caption" tint={color.danger}>{error}</AppText> : null}
      <Modal visible={open} transparent animationType="slide" onRequestClose={() => setOpen(false)}>
        <Pressable style={styles.backdrop} onPress={() => setOpen(false)} accessibilityLabel={t('common.close')} />
        <SafeAreaView edges={['bottom']} style={styles.sheet}>
          <View style={styles.grabber} />
          {label ? <AppText variant="h3" style={styles.sheetTitle}>{label}</AppText> : null}
          <FlatList
            data={options}
            keyExtractor={(o) => o.value}
            renderItem={({ item }) => {
              const on = item.value === value;
              return (
                <Pressable
                  onPress={() => { onChange(item.value); setOpen(false); }}
                  accessibilityRole="radio"
                  accessibilityState={{ checked: on }}
                  style={[styles.option, on && styles.optionOn]}
                >
                  <View style={styles.flex}>
                    <AppText>{item.label}</AppText>
                    {item.hint ? <AppText variant="caption" muted>{item.hint}</AppText> : null}
                  </View>
                  {on ? <Check color={color.primary} size={20} /> : null}
                </Pressable>
              );
            }}
          />
        </SafeAreaView>
      </Modal>
    </View>
  );
}

/** Row with the language's native name and greeting (S02, S37). */
export function LanguageOption({ language, selected, onPress }: { language: Language; selected: boolean; onPress: () => void }) {
  const { t } = useTranslation();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="radio"
      accessibilityState={{ checked: selected }}
      style={[styles.langRow, selected && styles.langOn]}
    >
      <View style={styles.flex}>
        <AppText variant="bodyMedium" textLanguage={language}>{t(`language.${language}`)}</AppText>
        <AppText variant="small" muted textLanguage={language}>{t(`language.greeting.${language}`)}</AppText>
      </View>
      <View style={[styles.radio, selected && styles.radioOn]}>{selected ? <Check color={color.onPrimary} size={14} /> : null}</View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  field: { gap: space.xs, minWidth: 0 },
  label: { color: color.textMuted },
  inputRow: {
    flexDirection: 'row', alignItems: 'center', gap: space.sm, minHeight: MIN_TOUCH + 6, paddingHorizontal: space.lg,
    borderWidth: 1.5, borderColor: 'transparent', borderRadius: radius.md, backgroundColor: color.fill,
  },
  focused: { borderColor: color.primary, backgroundColor: color.surface },
  errored: { borderColor: color.danger, backgroundColor: color.dangerTint },
  disabled: { opacity: 0.6 },
  input: { flex: 1, minWidth: 0, fontSize: 16, color: color.text, paddingVertical: space.md, outlineWidth: 0 } as object,
  backdrop: { flex: 1, backgroundColor: 'rgba(20,35,43,0.4)' },
  sheet: {
    backgroundColor: color.surface, borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, maxHeight: '70%',
    paddingHorizontal: space.lg, paddingBottom: space.lg,
  },
  grabber: { alignSelf: 'center', width: 40, height: 4, borderRadius: 2, backgroundColor: color.border, marginVertical: space.md },
  sheetTitle: { marginBottom: space.sm },
  option: { flexDirection: 'row', alignItems: 'center', minHeight: MIN_TOUCH, paddingVertical: space.md, paddingHorizontal: space.sm, borderRadius: radius.sm },
  optionOn: { backgroundColor: color.primaryTint },
  langRow: {
    flexDirection: 'row', alignItems: 'center', gap: space.md, minHeight: 64, padding: space.lg,
    borderWidth: 1.5, borderColor: 'transparent', borderRadius: radius.md, backgroundColor: color.surface, ...shadow,
  },
  langOn: { borderColor: color.primary, backgroundColor: color.primaryTint },
  radio: { width: 24, height: 24, borderRadius: 12, borderWidth: 2, borderColor: color.border, alignItems: 'center', justifyContent: 'center' },
  radioOn: { backgroundColor: color.primary, borderColor: color.primary },
});
