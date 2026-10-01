/**
 * Design tokens (spec §4.2). Components read only from here — no hard-coded colours or sizes.
 */
import type { TextStyle, ViewStyle } from 'react-native';

import type { Language } from '@/i18n';

export const color = {
  primary: '#0E5D66',
  primaryLight: '#1BA39C',
  primaryTint: '#E3F4F5',
  bg: '#F7FAFB',
  surface: '#FFFFFF',
  infoTint: '#E0F3FD',
  info: '#1F78B4',
  text: '#14232B',
  textMuted: '#5B6B73',
  border: '#E3EAEE',
  success: '#2E9E5B',
  successTint: '#E6F5EC',
  warning: '#E8A020',
  warningTint: '#FFF4DE',
  danger: '#D64545',
  dangerTint: '#FDECEC',
  skeleton: '#E9EEF1',
  onPrimary: '#FFFFFF',
} as const;

export const radius = { sm: 8, md: 16, lg: 24, pill: 999 } as const;

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 20, xxl: 24, xxxl: 32 } as const;

/** Single soft shadow: 0 2 8 rgba(20,35,43,0.06). */
export const shadow: ViewStyle = {
  shadowColor: '#14232B',
  shadowOffset: { width: 0, height: 2 },
  shadowOpacity: 0.06,
  shadowRadius: 8,
  elevation: 2,
};

export const MIN_TOUCH = 48;
export const MAX_CONTENT_WIDTH = 600;
export const SCREEN_PADDING = 16;

/** Font families as registered in app/_layout.tsx. */
export const fontFamily = {
  headingLatin: 'Poppins_600SemiBold',
  bodyLatin: 'Inter_400Regular',
  bodyLatinMedium: 'Inter_500Medium',
  headingDeva: 'NotoSansDevanagari_600SemiBold',
  bodyDeva: 'NotoSansDevanagari_400Regular',
  bodyDevaMedium: 'NotoSansDevanagari_500Medium',
  headingTamil: 'NotoSansTamil_600SemiBold',
  bodyTamil: 'NotoSansTamil_400Regular',
  bodyTamilMedium: 'NotoSansTamil_500Medium',
} as const;

export type FontRole = 'heading' | 'body' | 'bodyMedium';

/** Indic scripts need Noto; Poppins/Inter have no Devanagari or Tamil glyphs. */
export function fontFor(language: Language, role: FontRole): string {
  if (language === 'hi' || language === 'mr') {
    return role === 'heading' ? fontFamily.headingDeva : role === 'bodyMedium' ? fontFamily.bodyDevaMedium : fontFamily.bodyDeva;
  }
  if (language === 'ta') {
    return role === 'heading' ? fontFamily.headingTamil : role === 'bodyMedium' ? fontFamily.bodyTamilMedium : fontFamily.bodyTamil;
  }
  return role === 'heading' ? fontFamily.headingLatin : role === 'bodyMedium' ? fontFamily.bodyLatinMedium : fontFamily.bodyLatin;
}

export type TypeVariant = 'h1' | 'h2' | 'h3' | 'body' | 'bodyMedium' | 'small' | 'caption';

/** Type scale (size/line-height): h1 28/34, h2 22/28, h3 18/24, body 16/24, small 14/20, caption 12/16. */
export const typeScale: Record<TypeVariant, { size: number; line: number; role: FontRole }> = {
  h1: { size: 28, line: 34, role: 'heading' },
  h2: { size: 22, line: 28, role: 'heading' },
  h3: { size: 18, line: 24, role: 'heading' },
  body: { size: 16, line: 24, role: 'body' },
  bodyMedium: { size: 16, line: 24, role: 'bodyMedium' },
  small: { size: 14, line: 20, role: 'body' },
  caption: { size: 12, line: 16, role: 'body' },
};

/** Indic scripts have taller glyphs: give them ~15% more line height so marks aren't clipped. */
export function textStyle(variant: TypeVariant, language: Language): TextStyle {
  const t = typeScale[variant];
  const indic = language !== 'en';
  return {
    fontFamily: fontFor(language, t.role),
    fontSize: t.size,
    lineHeight: Math.round(t.line * (indic ? 1.15 : 1)),
    color: color.text,
  };
}

/** Max OS font scaling the layouts are designed for (spec §4.2: up to 1.3×). */
export const MAX_FONT_SCALE = 1.3;

export type Tone = 'info' | 'warning' | 'positive' | 'danger' | 'neutral';

export const toneColors: Record<Tone, { bg: string; fg: string }> = {
  info: { bg: color.infoTint, fg: color.info },
  warning: { bg: color.warningTint, fg: '#9A6406' },
  positive: { bg: color.successTint, fg: color.success },
  danger: { bg: color.dangerTint, fg: color.danger },
  neutral: { bg: color.primaryTint, fg: color.primary },
};
