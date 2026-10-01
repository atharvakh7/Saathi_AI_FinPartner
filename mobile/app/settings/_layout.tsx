/** Settings stack (S36–S40): logged-in users only. */
import { Redirect, Stack } from 'expo-router';

import { isLoggedIn, useSessionStore } from '@/stores/session';
import { color } from '@/theme';

export default function SettingsLayout() {
  const loggedIn = useSessionStore(isLoggedIn);
  if (!loggedIn) return <Redirect href="/onboarding/welcome" />;
  return <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: color.bg }, animation: 'slide_from_right' }} />;
}
