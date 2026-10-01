/** S03 Intro: two slides with page dots, Skip and Next / Get Started (spec §4.7). */
import { useRef, useState } from 'react';
import { ScrollView, StyleSheet, useWindowDimensions, View } from 'react-native';
import { router } from 'expo-router';
import { ArrowRight } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { AppText, Button, Mascot, Screen } from '@/components';
import { color, MAX_CONTENT_WIDTH, space } from '@/theme';

const SLIDES = [
  { pose: 'point_up', key: 'onboarding.intro.slide1' },
  { pose: 'shield', key: 'onboarding.intro.slide2' },
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
    <Screen scroll={false} padded={false}
      footer={
        <View style={styles.footer}>
          <Button label={t('common.skip')} variant="ghost" fullWidth={false} onPress={finish} />
          <View style={styles.dots} accessibilityLabel={`${index + 1} / ${SLIDES.length}`}>
            {SLIDES.map((s, i) => <View key={s.key} style={[styles.dot, i === index && styles.dotOn]} />)}
          </View>
          {last ? (
            <Button label={t('onboarding.intro.start')} fullWidth={false} onPress={finish} />
          ) : (
            <Button label={t('common.next')} fullWidth={false} icon={<ArrowRight color={color.onPrimary} size={18} />}
              onPress={() => go(index + 1)} />
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
            <Mascot pose={s.pose} size={220} />
            <AppText variant="h2" align="center">{t(`${s.key}.title`)}</AppText>
            <AppText muted align="center">{t(`${s.key}.body`)}</AppText>
          </View>
        ))}
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  slide: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: space.lg, paddingHorizontal: space.xxl },
  footer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: space.md },
  dots: { flexDirection: 'row', gap: space.sm },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: color.border },
  dotOn: { width: 22, backgroundColor: color.primary },
});
