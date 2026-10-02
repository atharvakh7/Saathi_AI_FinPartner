/**
 * Design tokens (spec §4.2). Components read only from here — no hard-coded colours or sizes.
 * Visual direction: minimal & clean — borderless white cards on a soft grey page, filled inputs and
 * chips, one quiet shadow, colour reserved for meaning (money in/out, status, risk).
 */
import type { TextStyle, ViewStyle } from 'react-native';

import type { Language } from '@/i18n';

export const color = {
  primary: '#0E5D66',
  primaryLight: '#1BA39C',
  primaryTint: '#E3F4F5',
  bg: '#F4F6F8',
  surface: '#FFFFFF',
  infoTint: '#E0F3FD',
  info: '#1F78B4',
  text: '#14232B',
  textMuted: '#5B6B73',
  border: '#E6EBEE',
  /** Filled inputs, chips, segmented controls, neutral icon backgrounds. */
  fill: '#EEF2F4',
  success: '#2E9E5B',
  successTint: '#E6F5EC',
  warning: '#E8A020',
  warningTint: '#FFF4DE',
  danger: '#D64545',
  dangerTint: '#FDECEC',
  skeleton: '#E9EEF1',
  onPrimary: '#FFFFFF',
  // Wireframe accent for savings / debt tiles (Financial Twin).
  accent: '#6C4FD8',
  accentTint: '#EFEBFD',
  // Soft teal glow behind the mascot on splash / intro.
  glow: '#CDEDEE',
} as const;

export const radius = { sm: 10, md: 18, lg: 24, pill: 999 } as const;

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 20, xxl: 24, xxxl: 32 } as const;

/** Single soft shadow: 0 4 16 rgba(20,35,43,0.05). */
export const shadow: ViewStyle = {
  shadowColor: '#14232B',
  shadowOffset: { width: 0, height: 4 },
  shadowOpacity: 0.05,
  shadowRadius: 16,
  elevation: 1,
};

export const MIN_TOUCH = 48;
export const MAX_CONTENT_WIDTH = 600;
export const SCREEN_PADDING = 20;

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

/** Type scale (size/line-height): h1 30/36, h2 22/28, h3 18/24, body 16/24, small 14/20, caption 12/16. */
export const typeScale: Record<TypeVariant, { size: number; line: number; role: FontRole }> = {
  h1: { size: 30, line: 36, role: 'heading' },
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
    // Slightly tighter Latin headings read cleaner; Indic scripts keep normal spacing.
    ...(t.role === 'heading' && !indic ? { letterSpacing: t.size >= 22 ? -0.4 : -0.2 } : null),
  };
}

/** Max OS font scaling the layouts are designed for (spec §4.2: up to 1.3×). */
export const MAX_FONT_SCALE = 1.3;

export type Tone = 'info' | 'warning' | 'positive' | 'danger' | 'neutral' | 'accent';

export const toneColors: Record<Tone, { bg: string; fg: string }> = {
  info: { bg: color.infoTint, fg: color.info },
  warning: { bg: color.warningTint, fg: '#9A6406' },
  positive: { bg: color.successTint, fg: color.success },
  danger: { bg: color.dangerTint, fg: color.danger },
  neutral: { bg: color.primaryTint, fg: color.primary },
  accent: { bg: color.accentTint, fg: color.accent },
};
