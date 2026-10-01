/**
 * Onboarding stack (S02–S09). Welcome/intro/phone/otp are public; the rest need a session
 * (spec §4.1 auth guard) — without one they redirect to Welcome.
 */
import { Redirect, Stack, useSegments } from 'expo-router';

import { isLoggedIn, useSessionStore } from '@/stores/session';
import { color } from '@/theme';

const PUBLIC = new Set(['welcome', 'intro', 'phone', 'otp']);

export default function OnboardingLayout() {
  const loggedIn = useSessionStore(isLoggedIn);
  const segments = useSegments();
  const screen = segments[segments.length - 1] ?? 'welcome';
  if (!loggedIn && !PUBLIC.has(screen)) return <Redirect href="/onboarding/welcome" />;
  return <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: color.bg }, animation: 'slide_from_right' }} />;
}
