/** S35 Profile (spec §4.7): who you are, settings rows, confidence score, version, log out. */
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import Constants from 'expo-constants';
import { router } from 'expo-router';
import { Bell, Brain, Gauge, Info, Languages, LogOut, Shield, UserPen } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { AppText, Card, Chip, ConfirmDialog, ErrorBanner, Mascot, PageHeader, Screen, SkeletonCard } from '@/components';
import { SettingsRow } from '@/features/settings/SettingsRow';
import { signOut, useMe } from '@/lib/session';
import { useLanguageStore } from '@/stores/language';
import { color, space } from '@/theme';

export default function Profile() {
  const { t } = useTranslation();
  const me = useMe();
  const language = useLanguageStore((s) => s.language);
  const [confirmLogout, setConfirmLogout] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const user = me.data?.user;
  const profile = me.data?.profile;
  const iconColor = color.primary;

  const logout = async () => {
    setLoggingOut(true);
    await signOut();
    setLoggingOut(false);
    setConfirmLogout(false);
    router.replace('/onboarding/welcome');
  };

  return (
    <Screen>
      <PageHeader title={t('tabs.profile')} pose={null} />
      {me.isPending ? <SkeletonCard /> : null}
      {me.error ? <ErrorBanner error={me.error} onRetry={() => void me.refetch()} /> : null}
      {user ? (
        <Card style={styles.header}>
          <Mascot pose="wave" size={64} variant="avatar" />
          <View style={styles.flex}>
            <AppText variant="h3">{profile?.full_name ?? user.first_name ?? ''}</AppText>
            <AppText muted>{user.phone_masked}</AppText>
            <View style={styles.chips}>
              <Chip label={t(`language.${language}`)} />
              {profile?.occupation_type ? <Chip label={t(`options.occupation.${profile.occupation_type}`)} /> : null}
            </View>
          </View>
        </Card>
      ) : null}

      <Card>
        <SettingsRow icon={<UserPen color={iconColor} size={20} />} label={t('settings.editProfile')} onPress={() => router.push('/settings/profile')} />
        <SettingsRow icon={<Languages color={iconColor} size={20} />} label={t('settings.language.title')}
          value={t(`language.${language}`)} onPress={() => router.push('/settings/language')} />
        <SettingsRow icon={<Bell color={iconColor} size={20} />} label={t('settings.notifications.title')}
          onPress={() => router.push('/settings/notifications')} />
        <SettingsRow icon={<Shield color={iconColor} size={20} />} label={t('settings.privacy.title')}
          onPress={() => router.push('/settings/privacy')} />
        <SettingsRow icon={<Brain color={iconColor} size={20} />} label={t('settings.memory.title')}
          onPress={() => router.push('/settings/memory')} />
      </Card>

      <Card>
        <SettingsRow
          icon={<Gauge color={iconColor} size={20} />}
          label={t('settings.confidence')}
          value={profile?.confidence_score_pct !== null && profile?.confidence_score_pct !== undefined
            ? `${profile.confidence_score_pct}% · ${t(`settings.confidenceLevel.${profile.confidence_level ?? 'low'}`)}`
            : t('settings.notTaken')}
          onPress={() => router.push({ pathname: '/onboarding/confidence', params: { retake: '1' } })}
        />
        <AppText variant="caption" muted style={styles.indent}>{t('settings.retake')}</AppText>
        <SettingsRow icon={<Info color={iconColor} size={20} />} label={t('settings.about')}
          value={t('settings.version', { version: Constants.expoConfig?.version ?? '0.1.0' })} />
      </Card>

      <Card>
        <SettingsRow icon={<LogOut color={color.danger} size={20} />} label={t('settings.logout')} danger onPress={() => setConfirmLogout(true)} />
      </Card>

      <ConfirmDialog visible={confirmLogout} title={t('settings.logoutConfirm')} confirmLabel={t('settings.logout')} danger
        loading={loggingOut} onConfirm={() => void logout()} onCancel={() => setConfirmLogout(false)} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', gap: space.md },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm, marginTop: space.xs },
  indent: { marginLeft: 40, marginTop: -space.sm },
});
