/**
 * S03 Intro (wireframe "Onboarding (3 screens)"): big left-aligned headline (the first one in teal),
 * a line of body text, a large mascot illustration; Skip + page dots + round arrow button, and a
 * "Get Started →" pill on the last slide.
 */
import { useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, useWindowDimensions, View } from 'react-native';
import { router } from 'expo-router';
import { ArrowRight, Mountain, Shield, Sparkles } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { AppText, Button, GradientBackground, Mascot, Screen } from '@/components';
import { color, MAX_CONTENT_WIDTH, shadow, space } from '@/theme';

const SLIDES = [
  { pose: 'wave', key: 'onboarding.intro.slide0', Deco: Sparkles, teal: true },
  { pose: 'point_up', key: 'onboarding.intro.slide1', Deco: Mountain, teal: false },
  { pose: 'shield', key: 'onboarding.intro.slide2', Deco: Shield, teal: false },
] as const;

export default function Intro() {
  const { t } = useTranslation();
  const { width: windowWidth } = useWindowDimensions();
  const width = Math.min(windowWidth, MAX_CONTENT_WIDTH);
  const [index, setIndex] = useState(0);
  const scroller = useRef<ScrollView>(null);
  const last = index === SLIDES.length - 1;
  const go = (i: number) => {
    scroller.current?.scrollTo({ x: i * width, animated: true });
    setIndex(i);
  };
  const finish = () => router.push('/onboarding/phone');

  return (
    <Screen scroll={false} padded={false} background={<GradientBackground />}
      footer={
        <View style={styles.footer}>
          <View style={styles.left}>
            <View style={styles.dots} accessibilityLabel={`${index + 1} / ${SLIDES.length}`}>
              {SLIDES.map((s, i) => <View key={s.key} style={[styles.dot, i === index && styles.dotOn]} />)}
            </View>
            {!last ? (
              <Pressable onPress={finish} hitSlop={10} accessibilityRole="button">
                <AppText muted>{t('common.skip')}</AppText>
              </Pressable>
            ) : null}
          </View>
          {last ? (
            <Button label={t('onboarding.intro.start')} fullWidth={false} onPress={finish} />
          ) : (
            <Pressable onPress={() => go(index + 1)} accessibilityRole="button" accessibilityLabel={t('common.next')}
              style={({ pressed }) => [styles.round, pressed && { opacity: 0.85 }]}>
              <ArrowRight color={color.onPrimary} size={24} />
            </Pressable>
          )}
        </View>
      }>
      <ScrollView
        ref={scroller}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={(e) => setIndex(Math.round(e.nativeEvent.contentOffset.x / width))}
      >
        {SLIDES.map((s) => (
          <View key={s.key} style={[styles.slide, { width }]}>
            <View style={styles.text}>
              <AppText variant="h1" tint={s.teal ? color.primaryLight : color.text} style={styles.title}>{t(`${s.key}.title`)}</AppText>
              <AppText muted>{t(`${s.key}.body`)}</AppText>
            </View>
            <View style={styles.art}>
              <View style={styles.glow} />
              <View style={styles.deco}><s.Deco color={color.primaryLight} size={30} /></View>
              <Mascot pose={s.pose} size={320} />
            </View>
          </View>
        ))}
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  slide: { flex: 1, paddingHorizontal: space.xxl, paddingTop: space.xxxl, gap: space.xl },
  text: { gap: space.sm },
  title: { fontSize: 34, lineHeight: 42 },
  art: { flex: 1, alignItems: 'center', justifyContent: 'flex-end', paddingBottom: space.lg },
  glow: { position: 'absolute', bottom: 40, width: 290, height: 290, borderRadius: 145, backgroundColor: color.glow, opacity: 0.55 },
  deco: {
    position: 'absolute', top: '12%', right: '10%', width: 56, height: 56, borderRadius: 28, backgroundColor: color.surface,
    alignItems: 'center', justifyContent: 'center', ...shadow,
  },
  footer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: space.md, minHeight: 64 },
  left: { gap: space.sm },
  dots: { flexDirection: 'row', gap: space.sm },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: color.border },
  dotOn: { width: 22, backgroundColor: color.primary },
  round: {
    width: 56, height: 56, borderRadius: 28, backgroundColor: color.primary, alignItems: 'center', justifyContent: 'center', ...shadow,
  },
});
