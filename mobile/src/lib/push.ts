/**
 * Push notifications (spec §4.9): ask permission, get the Expo push token, register it with
 * POST /me/device-tokens, and open the right screen when a notification is tapped.
 *
 * Works on a development / production build with EXPO_PUBLIC_EAS_PROJECT_ID set. It is skipped
 * (returns a reason) on web, in simulators/emulators without Google Play services, and in Expo Go on
 * Android, which no longer supports remote push (SDK 53+). In-app notifications (S13) work everywhere.
 */
import { Platform } from 'react-native';
import Constants, { ExecutionEnvironment } from 'expo-constants';
import * as Device from 'expo-device';
import { router } from 'expo-router';
import * as Notifications from 'expo-notifications';

import { registerDeviceToken } from '@/api/endpoints';
import { config } from '@/config';
import { appRoute } from './routes';

export type PushResult = 'registered' | 'denied' | 'unsupported' | 'no_project' | 'error';

/** Whether this runtime can receive remote push at all. */
export function pushSupported(): boolean {
  if (Platform.OS === 'web' || !Device.isDevice) return false;
  const expoGo = Constants.executionEnvironment === ExecutionEnvironment.StoreClient;
  return !(expoGo && Platform.OS === 'android');
}

export async function registerForPush(askPermission: boolean): Promise<PushResult> {
  if (!pushSupported()) return 'unsupported';
  if (!config.easProjectId) return 'no_project';
  try {
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', { name: 'Saathi', importance: Notifications.AndroidImportance.DEFAULT });
    }
    let { status } = await Notifications.getPermissionsAsync();
    if (status !== 'granted' && askPermission) status = (await Notifications.requestPermissionsAsync()).status;
    if (status !== 'granted') return 'denied';
    const token = (await Notifications.getExpoPushTokenAsync({ projectId: config.easProjectId })).data;
    await registerDeviceToken(token, Platform.OS === 'ios' ? 'ios' : 'android');
    return 'registered';
  } catch {
    return 'error';
  }
}

let listening = false;

/** Show notifications while the app is open, and route taps to their screen. Call once at start-up. */
export function setupNotificationHandling(): void {
  if (listening || Platform.OS === 'web') return;
  listening = true;
  Notifications.setNotificationHandler({
    handleNotification: async () => ({ shouldShowBanner: true, shouldShowList: true, shouldPlaySound: false, shouldSetBadge: false }),
  });
  Notifications.addNotificationResponseReceivedListener((res) => {
    const route = appRoute((res.notification.request.content.data as { route?: string } | undefined)?.route);
    if (route) router.push(route as never);
  });
}
