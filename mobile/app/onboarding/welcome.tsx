/**
 * S02 Welcome (wireframe "Splash"): logo mark + wordmark, tagline, the four verbs, large waving
 * mascot on a soft glow, language dropdown, Get Started — on a white-to-teal wash.
 */
import { StyleSheet, View } from 'react-native';
import { Redirect, router } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { AppText, Button, GradientBackground, Logo, Mascot, Screen, Select } from '@/components';
import { LANGUAGES, type Language } from '@/i18n';
import { useLanguageStore } from '@/stores/language';
import { isLoggedIn, useSessionStore } from '@/stores/session';
import { color, space } from '@/theme';

export default function Welcome() {
  const { t } = useTranslation();
  const loggedIn = useSessionStore(isLoggedIn);
  const language = useLanguageStore((s) => s.language);
  const setLanguage = useLanguageStore((s) => s.setLanguage);
  if (loggedIn) return <Redirect href="/" />;

  return (
    <Screen background={<GradientBackground />}
      footer={<Button label={t('onboarding.welcome.start')} onPress={() => router.push('/onboarding/intro')} />}>
      <View style={styles.brand}>
        <Logo size={64} />
        <AppText variant="bodyMedium" align="center">{t('onboarding.welcome.tagline')}</AppText>
        <AppText variant="small" muted align="center">{t('onboarding.welcome.subtitle')}</AppText>
      </View>
      <View style={styles.hero}>
        <View style={styles.glow} />
        <Mascot pose="wave" size={330} />
      </View>
      <Select<Language>
        label={t('onboarding.welcome.language')}
        value={language}
        onChange={(l) => void setLanguage(l, { syncServer: false })}
        options={LANGUAGES.map((l) => ({ value: l, label: t(`language.${l}`) }))}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  brand: { alignItems: 'center', gap: space.xs, paddingTop: space.lg },
  hero: { flex: 1, alignItems: 'center', justifyContent: 'flex-end', minHeight: 340 },
  glow: { position: 'absolute', bottom: 20, width: 300, height: 300, borderRadius: 150, backgroundColor: color.glow, opacity: 0.6 },
});
