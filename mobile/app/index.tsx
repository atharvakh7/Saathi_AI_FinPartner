/**
 * S01 Splash/Router: with no session -> welcome; otherwise GET /me and go to the first unfinished
 * onboarding step, or home (spec §4.1 auth guard).
 */
import { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import { Redirect } from 'expo-router';
import { useQuery } from '@tanstack/react-query';

import { api } from '@/api/client';
import type { MeDTO } from '@/api/types';
import { ErrorBanner, Mascot } from '@/components';
import { isLanguage } from '@/i18n';
import { routeForSession } from '@/lib/routing';
import { useLanguageStore } from '@/stores/language';
import { isLoggedIn, useSessionStore } from '@/stores/session';
import { color, space } from '@/theme';

export default function Index() {
  const loggedIn = useSessionStore(isLoggedIn);
  const me = useQuery({
    queryKey: ['me'],
    queryFn: async () => (await api.get<MeDTO>('/me')).data,
    enabled: loggedIn,
  });

  useEffect(() => {
    if (!me.data) return;
    useSessionStore.getState().setUser(me.data.user);
    const serverLanguage = me.data.user.preferred_language;
    if (isLanguage(serverLanguage) && serverLanguage !== useLanguageStore.getState().language) {
      void useLanguageStore.getState().setLanguage(serverLanguage, { syncServer: false });
    }
  }, [me.data]);

  if (!loggedIn) return <Redirect href={routeForSession(false, null) as never} />;
  if (me.data) return <Redirect href={routeForSession(true, me.data) as never} />;
  return (
    <View style={styles.center}>
      <Mascot pose="wave" size={220} />
      {me.isError ? (
        <View style={styles.error}>
          <ErrorBanner error={me.error} onRetry={() => void me.refetch()} />
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: color.bg, gap: space.xxl },
  error: { alignSelf: 'stretch', paddingHorizontal: space.lg },
});
