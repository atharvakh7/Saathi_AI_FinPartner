/**
 * Small key-value storage for tokens and the chosen language (spec §4.3: expo-secure-store).
 * On web (used only for development previews) SecureStore isn't available, so localStorage is used.
 */
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

export const KEYS = {
  accessToken: 'access_token',
  refreshToken: 'refresh_token',
  language: 'lang',
} as const;

const web = Platform.OS === 'web';

export async function getItem(key: string): Promise<string | null> {
  try {
    if (web) return globalThis.localStorage?.getItem(key) ?? null;
    return await SecureStore.getItemAsync(key);
  } catch {
    return null; // a corrupted keystore entry must not crash start-up
  }
}

export async function setItem(key: string, value: string): Promise<void> {
  if (web) {
    globalThis.localStorage?.setItem(key, value);
    return;
  }
  await SecureStore.setItemAsync(key, value);
}

export async function deleteItem(key: string): Promise<void> {
  try {
    if (web) {
      globalThis.localStorage?.removeItem(key);
      return;
    }
    await SecureStore.deleteItemAsync(key);
  } catch {
    // already gone
  }
}
