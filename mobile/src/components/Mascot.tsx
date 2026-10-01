/** Mascot image + MascotBubble (spec §4.2 poses, §4.4). A gentle idle bounce unless reduced motion is on. */
import { useEffect } from 'react';
import { AccessibilityInfo, StyleSheet, View } from 'react-native';
import { Image } from 'expo-image';
import Animated, { useAnimatedStyle, useSharedValue, withRepeat, withSequence, withTiming } from 'react-native-reanimated';
import { useTranslation } from 'react-i18next';

import { color, radius, shadow, space } from '@/theme';
import { AppText } from './AppText';

export type MascotPose = 'wave' | 'point_up' | 'shield' | 'listening' | 'speaking' | 'thumbs_up' | 'thinking';

const SOURCES: Record<MascotPose, number> = {
  wave: require('../../assets/mascot/wave.png'),
  point_up: require('../../assets/mascot/point_up.png'),
  shield: require('../../assets/mascot/shield.png'),
  listening: require('../../assets/mascot/listening.png'),
  speaking: require('../../assets/mascot/speaking.png'),
  thumbs_up: require('../../assets/mascot/thumbs_up.png'),
  thinking: require('../../assets/mascot/thinking.png'),
};

export function isMascotPose(value: unknown): value is MascotPose {
  return typeof value === 'string' && value in SOURCES;
}

export function Mascot({ pose = 'wave', size = 120, bounce = true }: { pose?: MascotPose; size?: number; bounce?: boolean }) {
  const { t } = useTranslation();
  const y = useSharedValue(0);
  useEffect(() => {
    let cancelled = false;
    void AccessibilityInfo.isReduceMotionEnabled().then((reduce) => {
      if (cancelled || reduce || !bounce) return;
      y.value = withRepeat(withSequence(withTiming(-4, { duration: 900 }), withTiming(0, { duration: 900 })), -1);
    });
    return () => {
      cancelled = true;
    };
  }, [bounce, y]);
  const anim = useAnimatedStyle(() => ({ transform: [{ translateY: y.value }] }));
  return (
    <Animated.View style={anim} accessible accessibilityRole="image" accessibilityLabel={t('mascot.alt')}>
      <Image source={SOURCES[pose]} style={{ width: size, height: size }} contentFit="contain" />
    </Animated.View>
  );
}

export function MascotBubble({ pose = 'wave', text, size = 96 }: { pose?: MascotPose; text: string; size?: number }) {
  return (
    <View style={styles.row}>
      <Mascot pose={pose} size={size} />
      <View style={styles.bubble}>
        <AppText>{text}</AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: space.sm },
  bubble: {
    flex: 1, backgroundColor: color.surface, borderRadius: radius.md, borderTopLeftRadius: radius.sm, padding: space.lg,
    borderWidth: 1, borderColor: color.border, ...shadow,
  },
});
