/**
 * Main tab bar (spec §4.2 layout, §4.5): Home, Plan, Saathi (raised circular mic in primary),
 * Learn, Profile. Guard: no session -> Welcome; onboarding unfinished -> its next step.
 */
import type { ReactNode } from 'react';
import { Platform, Pressable, StyleSheet, View } from 'react-native';
import { Redirect, Tabs } from 'expo-router';
import { BookOpen, ChartNoAxesColumn, House, Mic, UserRound } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { AppText } from '@/components';
import { routeForSession } from '@/lib/routing';
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
          height: 64 + insets.bottom, paddingBottom: insets.bottom + (Platform.OS === 'ios' ? 0 : 6), paddingTop: 6,
          backgroundColor: color.surface, borderTopColor: color.border,
        },
        sceneStyle: { backgroundColor: color.bg },
      }}
    >
      <Tabs.Screen name="home" options={{ title: t('tabs.home'), tabBarIcon: icon(House), tabBarLabel: label('tabs.home') }} />
      <Tabs.Screen name="plan" options={{ title: t('tabs.plan'), tabBarIcon: icon(ChartNoAxesColumn), tabBarLabel: label('tabs.plan') }} />
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
      <Tabs.Screen name="learn" options={{ title: t('tabs.learn'), tabBarIcon: icon(BookOpen), tabBarLabel: label('tabs.learn') }} />
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
