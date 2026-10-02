/**
 * Mascot (spec §4.2 poses, §4.4) — the 3D character, tightly cropped PNGs (no padding), so `size` is
 * the visible height. Three ways to show him:
 *  - full:   the whole figure (welcome, intro, empty states);
 *  - bust:   head and shoulders, centred on the face (page headers, speech bubbles);
 *  - avatar: the bust inside a circle (chat header, voice mode).
 * A gentle idle bounce unless reduced motion is on (full figures only).
 */
import { useEffect } from 'react';
import { AccessibilityInfo, StyleSheet, View } from 'react-native';
import { Image } from 'expo-image';
import Animated, { useAnimatedStyle, useSharedValue, withRepeat, withSequence, withTiming } from 'react-native-reanimated';
import { useTranslation } from 'react-i18next';

import { color, radius, shadow, space } from '@/theme';
import { AppText } from './AppText';

export type MascotPose = 'wave' | 'point_up' | 'shield' | 'listening' | 'speaking' | 'thumbs_up' | 'thinking' | 'greeting';
export type MascotVariant = 'full' | 'bust' | 'avatar';

const SOURCES: Record<MascotPose, number> = {
  wave: require('../../assets/mascot/wave.png'),
  point_up: require('../../assets/mascot/point_up.png'),
  shield: require('../../assets/mascot/shield.png'),
  listening: require('../../assets/mascot/listening.png'),
  speaking: require('../../assets/mascot/speaking.png'),
  thumbs_up: require('../../assets/mascot/thumbs_up.png'),
  thinking: require('../../assets/mascot/thinking.png'),
  greeting: require('../../assets/mascot/greeting.png'),
};

/** width / height of each cropped pose, and where the face is (fraction of the width). */
const ASPECT: Record<MascotPose, number> = {
  wave: 0.6357, point_up: 0.5757, shield: 0.6114, listening: 0.6314, speaking: 0.6386, thumbs_up: 0.5686, thinking: 0.5414, greeting: 0.64,
};
const FACE_X: Record<MascotPose, number> = {
  wave: 0.607, point_up: 0.583, shield: 0.554, listening: 0.44, speaking: 0.461, thumbs_up: 0.408, thinking: 0.556, greeting: 0.506,
};
/** Share of the figure's height shown in bust mode (head, shoulders, top of the hoodie). */
const BUST = 0.52;

export function isMascotPose(value: unknown): value is MascotPose {
  return typeof value === 'string' && value in SOURCES;
}

export function Mascot({ pose = 'wave', size = 120, bounce = true, variant = 'full', ringColor }: {
  pose?: MascotPose; size?: number; bounce?: boolean; variant?: MascotVariant; ringColor?: string;
}) {
  const { t } = useTranslation();
  const y = useSharedValue(0);
  const animate = bounce && variant === 'full';
  useEffect(() => {
    let cancelled = false;
    void AccessibilityInfo.isReduceMotionEnabled().then((reduce) => {
      if (cancelled || reduce || !animate) return;
      y.value = withRepeat(withSequence(withTiming(-4, { duration: 900 }), withTiming(0, { duration: 900 })), -1);
    });
    return () => {
      cancelled = true;
    };
  }, [animate, y]);
  const anim = useAnimatedStyle(() => ({ transform: [{ translateY: y.value }] }));
  const aspect = ASPECT[pose];

  if (variant === 'full') {
    return (
      <Animated.View style={anim} accessible accessibilityRole="image" accessibilityLabel={t('mascot.alt')}>
        <Image source={SOURCES[pose]} style={{ width: size * aspect, height: size }} contentFit="contain" />
      </Animated.View>
    );
  }

  // Bust / avatar: scale the figure so the top BUST share fills the box, centre on the face, clip.
  const avatar = variant === 'avatar';
  const imgH = avatar ? size * 1.75 : size / BUST;
  const imgW = imgH * aspect;
  const boxW = avatar ? size : Math.min(imgW, size * 1.05);
  const left = Math.max(boxW - imgW, Math.min(0, boxW / 2 - FACE_X[pose] * imgW));
  return (
    <View accessible accessibilityRole="image" accessibilityLabel={t('mascot.alt')}
      style={[{ width: boxW, height: size, overflow: 'hidden' },
        avatar && { borderRadius: size / 2, backgroundColor: ringColor ?? color.primaryTint }]}>
      <Image source={SOURCES[pose]} contentFit="contain"
        style={{ position: 'absolute', width: imgW, height: imgH, left, top: avatar ? size * 0.08 : 0 }} />
    </View>
  );
}

export function MascotBubble({ pose = 'wave', text, size = 84 }: { pose?: MascotPose; text: string; size?: number }) {
  return (
    <View style={styles.row}>
      <Mascot pose={pose} size={size} variant="bust" />
      <View style={styles.bubble}>
        <AppText>{text}</AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'flex-end', gap: space.sm },
  bubble: {
    flex: 1, backgroundColor: color.surface, borderRadius: radius.md, borderBottomLeftRadius: radius.sm, padding: space.lg,
    marginBottom: space.sm, ...shadow,
  },
});
