/** S02 Welcome: logo, tagline, language dropdown, Get Started (spec §4.7). */
import { StyleSheet, View } from 'react-native';
import { Redirect, router } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { AppText, Button, Mascot, Screen, Select } from '@/components';
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
    <Screen footer={<Button label={t('onboarding.welcome.start')} onPress={() => router.push('/onboarding/intro')} />}>
      <View style={styles.hero}>
        <Mascot pose="wave" size={200} />
        <AppText variant="h1" tint={color.primary} align="center">{t('common.appName')}</AppText>
        <AppText variant="h3" align="center">{t('onboarding.welcome.tagline')}</AppText>
        <AppText muted align="center">{t('onboarding.welcome.subtitle')}</AppText>
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
  hero: { alignItems: 'center', gap: space.md, paddingTop: space.xxl },
});
