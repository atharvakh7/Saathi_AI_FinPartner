/**
 * All text goes through AppText so every string gets the right script font (Noto for hi/mr/ta)
 * and the type scale (spec §4.2). `textLanguage` overrides the UI language for mixed content
 * (e.g. a Hindi reply shown while the UI is in English).
 */
import { Text, type TextProps, type TextStyle } from 'react-native';

import type { Language } from '@/i18n';
import { useLanguageStore } from '@/stores/language';
import { color, MAX_FONT_SCALE, textStyle, type TypeVariant } from '@/theme';

export interface AppTextProps extends TextProps {
  variant?: TypeVariant;
  muted?: boolean;
  tint?: string;
  align?: TextStyle['textAlign'];
  textLanguage?: Language | null;
}

/** Scripts present in a string decide the font when no language is given. */
export function scriptLanguage(text: string, fallback: Language): Language {
  if (/[஀-௿]/.test(text)) return 'ta'; // Tamil block
  if (/[ऀ-ॿ]/.test(text)) return fallback === 'mr' ? 'mr' : 'hi'; // Devanagari block
  return fallback;
}

export function AppText({ variant = 'body', muted, tint, align, textLanguage, style, children, ...rest }: AppTextProps) {
  const uiLanguage = useLanguageStore((s) => s.language);
  const content = typeof children === 'string' ? children : '';
  const language = textLanguage ?? (content ? scriptLanguage(content, uiLanguage) : uiLanguage);
  return (
    <Text
      maxFontSizeMultiplier={MAX_FONT_SCALE}
      style={[textStyle(variant, language), muted && { color: color.textMuted }, tint ? { color: tint } : null,
        align ? { textAlign: align } : null, style]}
      {...rest}
    >
      {children}
    </Text>
  );
}
