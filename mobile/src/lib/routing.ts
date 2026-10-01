/** Where a session should land (spec §4.1 auth guard, S01). */
import type { MeDTO, OnboardingStep } from '@/api/types';

const STEP_ROUTES: Record<OnboardingStep, string> = {
  consent: '/onboarding/consent',
  profile: '/onboarding/profile',
  confidence: '/onboarding/confidence',
  goals: '/onboarding/goals',
};

export const WELCOME_ROUTE = '/onboarding/welcome';
export const HOME_ROUTE = '/home';

export function routeForSession(loggedIn: boolean, me: MeDTO | null): string {
  if (!loggedIn) return WELCOME_ROUTE;
  if (!me) return WELCOME_ROUTE;
  if (me.needs) return STEP_ROUTES[me.needs];
  return me.user.onboarding_completed_at ? HOME_ROUTE : STEP_ROUTES.consent;
}
