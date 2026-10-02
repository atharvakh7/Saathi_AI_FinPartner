/**
 * Main tab bar (wireframe): Home, Services, Saathi (raised circular mic in primary), Goals, Profile.
 * Plan and Learn are reached from Services. Guard: no session -> Welcome; onboarding unfinished -> its next step.
 */
import { useEffect, type ReactNode } from 'react';
import { Platform, Pressable, StyleSheet, View } from 'react-native';
import { Redirect, Tabs } from 'expo-router';
import { House, LayoutGrid, Mic, Target, UserRound } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { AppText } from '@/components';
import { routeForSession } from '@/lib/routing';
import { registerForPush } from '@/lib/push';
import { useMe } from '@/lib/session';
import { isLoggedIn, useSessionStore } from '@/stores/session';
import { color, MIN_TOUCH, shadow } from '@/theme';

const ICON = 24;

function Label({ text, focused }: { text: string; focused: boolean }) {
  return (
    <AppText variant="caption" tint={focused ? color.primary : color.textMuted} numberOfLines={1}>{text}</AppText>
  );
}

function SaathiButton({ onPress, label, focused }: {
  onPress?: React.ComponentProps<typeof Pressable>['onPress']; label: string; focused: boolean;
}) {
  return (
    <Pressable onPress={onPress} accessibilityRole="tab" accessibilityLabel={label} accessibilityState={{ selected: focused }}
      style={styles.saathiWrap}>
      <View style={styles.saathi}>
        <Mic color={color.onPrimary} size={28} />
      </View>
      <Label text={label} focused={focused} />
    </Pressable>
  );
}

export default function TabsLayout() {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const loggedIn = useSessionStore(isLoggedIn);
  const me = useMe();
  const ready = !!me.data && !me.data.needs;
  // Keep this device's push token registered (no permission prompt here; settings ask for it).
  useEffect(() => { if (ready) void registerForPush(false); }, [ready]);
  if (!loggedIn) return <Redirect href="/onboarding/welcome" />;
  if (me.data && me.data.needs) return <Redirect href={routeForSession(true, me.data) as never} />;

  const icon = (Icon: typeof House) => ({ focused }: { focused: boolean }): ReactNode =>
    <Icon color={focused ? color.primary : color.textMuted} size={ICON} />;
  const label = (key: string) => ({ focused }: { focused: boolean }) => <Label text={t(key)} focused={focused} />;

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: color.primary,
        tabBarInactiveTintColor: color.textMuted,
        tabBarStyle: {
          height: 66 + insets.bottom, paddingBottom: insets.bottom + (Platform.OS === 'ios' ? 0 : 8), paddingTop: 8,
          backgroundColor: color.surface, borderTopWidth: 0, ...shadow,
        },
        sceneStyle: { backgroundColor: color.bg },
      }}
    >
      <Tabs.Screen name="home" options={{ title: t('tabs.home'), tabBarIcon: icon(House), tabBarLabel: label('tabs.home') }} />
      <Tabs.Screen name="services" options={{ title: t('tabs.services'), tabBarIcon: icon(LayoutGrid), tabBarLabel: label('tabs.services') }} />
      <Tabs.Screen
        name="saathi"
        options={{
          title: t('tabs.saathi'),
          tabBarButton: (props) => (
            <SaathiButton onPress={props.onPress ?? undefined} label={t('tabs.saathi')}
              focused={!!props.accessibilityState?.selected || props['aria-selected'] === true} />
          ),
        }}
      />
      <Tabs.Screen name="goals" options={{ title: t('tabs.goals'), tabBarIcon: icon(Target), tabBarLabel: label('tabs.goals') }} />
      <Tabs.Screen name="profile" options={{ title: t('tabs.profile'), tabBarIcon: icon(UserRound), tabBarLabel: label('tabs.profile') }} />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  saathiWrap: { flex: 1, alignItems: 'center', justifyContent: 'flex-end', minWidth: MIN_TOUCH },
  saathi: {
    width: 60, height: 60, borderRadius: 30, backgroundColor: color.primary, alignItems: 'center', justifyContent: 'center',
    marginTop: -26, borderWidth: 4, borderColor: color.surface, ...shadow,
  },
});
