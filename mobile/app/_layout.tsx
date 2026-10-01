/**
 * Root layout: fonts, providers, API wiring, session + language hydration, splash screen.
 */
import { useEffect, useState } from 'react';
import { StyleSheet } from 'react-native';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useFonts } from 'expo-font';
import { QueryClientProvider } from '@tanstack/react-query';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Inter_400Regular } from '@expo-google-fonts/inter/400Regular';
import { Inter_500Medium } from '@expo-google-fonts/inter/500Medium';
import { NotoSansDevanagari_400Regular } from '@expo-google-fonts/noto-sans-devanagari/400Regular';
import { NotoSansDevanagari_500Medium } from '@expo-google-fonts/noto-sans-devanagari/500Medium';
import { NotoSansDevanagari_600SemiBold } from '@expo-google-fonts/noto-sans-devanagari/600SemiBold';
import { NotoSansTamil_400Regular } from '@expo-google-fonts/noto-sans-tamil/400Regular';
import { NotoSansTamil_500Medium } from '@expo-google-fonts/noto-sans-tamil/500Medium';
import { NotoSansTamil_600SemiBold } from '@expo-google-fonts/noto-sans-tamil/600SemiBold';
import { Poppins_600SemiBold } from '@expo-google-fonts/poppins/600SemiBold';

import '@/i18n';
import { queryClient } from '@/api/queryClient';
import { setupApi } from '@/api/setup';
import { Toast } from '@/components';
import { useLanguageStore } from '@/stores/language';
import { useSessionStore } from '@/stores/session';
import { color } from '@/theme';

void SplashScreen.preventAutoHideAsync().catch(() => undefined);
setupApi();

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    Poppins_600SemiBold, Inter_400Regular, Inter_500Medium,
    NotoSansDevanagari_400Regular, NotoSansDevanagari_500Medium, NotoSansDevanagari_600SemiBold,
    NotoSansTamil_400Regular, NotoSansTamil_500Medium, NotoSansTamil_600SemiBold,
  });
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    void Promise.all([
      useSessionStore.getState().hydrateFromSecureStore(),
      useLanguageStore.getState().hydrate(),
    ]).finally(() => setHydrated(true));
  }, []);

  // A font that fails to load falls back to the system font rather than blocking the app.
  const ready = (fontsLoaded || !!fontError) && hydrated;
  useEffect(() => {
    if (ready) void SplashScreen.hideAsync().catch(() => undefined);
  }, [ready]);

  if (!ready) return null;
  return (
    <GestureHandlerRootView style={styles.root}>
      <SafeAreaProvider>
        <QueryClientProvider client={queryClient}>
          <StatusBar style="dark" />
          <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: color.bg }, animation: 'slide_from_right' }} />
          <Toast />
        </QueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({ root: { flex: 1, backgroundColor: color.bg } });
