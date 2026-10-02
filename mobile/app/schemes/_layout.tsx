/** Scheme Scout stack (S23–S27): logged-in users only. */
import { Redirect, Stack } from 'expo-router';

import { isLoggedIn, useSessionStore } from '@/stores/session';
import { color } from '@/theme';

export default function SchemesLayout() {
  const loggedIn = useSessionStore(isLoggedIn);
  if (!loggedIn) return <Redirect href="/onboarding/welcome" />;
  return <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: color.bg }, animation: 'slide_from_right' }} />;
}
