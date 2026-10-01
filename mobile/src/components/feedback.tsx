/** EmptyState, ErrorBanner, Skeleton, Toast, ConfirmDialog, OfflineBanner (spec §4.1, §4.4). */
import { useEffect, useRef } from 'react';
import { Animated, Modal, Pressable, StyleSheet, View, type DimensionValue } from 'react-native';
import { useNetworkState } from 'expo-network';
import { CircleAlert, WifiOff } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { useUiStore } from '@/stores';
import { color, radius, shadow, space, toneColors } from '@/theme';
import { AppText } from './AppText';
import { Button } from './Button';
import { Mascot, type MascotPose } from './Mascot';

export function EmptyState({ pose = 'wave', message, actionLabel, onAction }: {
  pose?: MascotPose; message: string; actionLabel?: string; onAction?: () => void;
}) {
  return (
    <View style={styles.empty}>
      <Mascot pose={pose} size={140} />
      <AppText align="center" muted>{message}</AppText>
      {actionLabel && onAction ? <Button label={actionLabel} onPress={onAction} fullWidth={false} /> : null}
    </View>
  );
}

/** Localized message for any error: `errors.<CODE>`, else the server message. */
export function useErrorMessage() {
  const { t, i18n } = useTranslation();
  return (error: unknown): string => {
    const code = error instanceof ApiError ? error.code : 'INTERNAL';
    const key = `errors.${code}`;
    if (i18n.exists(key)) return t(key);
    return error instanceof ApiError ? error.message : t('errors.INTERNAL');
  };
}

export function ErrorBanner({ error, onRetry, message: override }: { error?: unknown; onRetry?: () => void; message?: string }) {
  const { t } = useTranslation();
  const toMessage = useErrorMessage();
  const message = override ?? toMessage(error);
  return (
    <View style={[styles.banner, { backgroundColor: toneColors.danger.bg }]} accessibilityRole="alert">
      <CircleAlert color={color.danger} size={20} />
      <AppText variant="small" tint={color.danger} style={styles.flex}>{message}</AppText>
      {onRetry ? <Button label={t('common.tryAgain')} variant="ghost" size="sm" fullWidth={false} onPress={onRetry} /> : null}
    </View>
  );
}

/** Grey rounded placeholder that gently pulses (spec §4.1: skeletons, never a blocking spinner). */
export function Skeleton({ width = '100%', height = 16, rounded = radius.md }: {
  width?: DimensionValue; height?: number; rounded?: number;
}) {
  const opacity = useRef(new Animated.Value(0.5)).current;
  useEffect(() => {
    const loop = Animated.loop(Animated.sequence([
      Animated.timing(opacity, { toValue: 1, duration: 700, useNativeDriver: true }),
      Animated.timing(opacity, { toValue: 0.5, duration: 700, useNativeDriver: true }),
    ]));
    loop.start();
    return () => loop.stop();
  }, [opacity]);
  return <Animated.View style={{ width, height, borderRadius: rounded, backgroundColor: color.skeleton, opacity }} />;
}

export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <View style={styles.skeletonCard}>
      <Skeleton width="50%" height={18} />
      {Array.from({ length: lines }, (_, i) => <Skeleton key={i} width={i === lines - 1 ? '70%' : '100%'} />)}
    </View>
  );
}

export function Toast() {
  const toast = useUiStore((s) => s.toast);
  const hide = useUiStore((s) => s.hideToast);
  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(hide, 3500);
    return () => clearTimeout(id);
  }, [toast, hide]);
  if (!toast) return null;
  const tone = toast.type === 'error' ? toneColors.danger : toast.type === 'success' ? toneColors.positive : toneColors.info;
  return (
    <Pressable onPress={hide} style={[styles.toast, { backgroundColor: tone.bg }]} accessibilityRole="alert"
      accessibilityLiveRegion="polite">
      <AppText variant="small" tint={tone.fg}>{toast.message}</AppText>
    </Pressable>
  );
}

export function ConfirmDialog({ visible, title, message, confirmLabel, cancelLabel, danger, loading, confirmDisabled, onConfirm, onCancel, children }: {
  visible: boolean; title: string; message?: string; confirmLabel: string; cancelLabel?: string; danger?: boolean;
  loading?: boolean; confirmDisabled?: boolean; onConfirm: () => void; onCancel: () => void; children?: React.ReactNode;
}) {
  const { t } = useTranslation();
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onCancel}>
      <View style={styles.backdrop}>
        <View style={styles.dialog} accessibilityViewIsModal>
          <AppText variant="h3">{title}</AppText>
          {message ? <AppText muted>{message}</AppText> : null}
          {children}
          <View style={styles.dialogButtons}>
            <Button label={cancelLabel ?? t('common.cancel')} variant="secondary" onPress={onCancel} style={styles.flex} />
            <Button label={confirmLabel} variant={danger ? 'danger' : 'primary'} onPress={onConfirm} loading={loading} disabled={confirmDisabled} style={styles.flex} />
          </View>
        </View>
      </View>
    </Modal>
  );
}

/** "You're offline" (spec §4.1). isInternetReachable can be null while unknown: only `false` counts. */
export function OfflineBanner() {
  const { t } = useTranslation();
  const net = useNetworkState();
  if (net.isConnected !== false && net.isInternetReachable !== false) return null;
  return (
    <View style={styles.offline} accessibilityRole="alert">
      <WifiOff color={color.onPrimary} size={16} />
      <AppText variant="small" tint={color.onPrimary}>{t('common.offline')}</AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  empty: { alignItems: 'center', gap: space.lg, paddingVertical: space.xxxl, paddingHorizontal: space.xl },
  banner: { flexDirection: 'row', alignItems: 'center', gap: space.sm, padding: space.md, borderRadius: radius.md },
  skeletonCard: {
    backgroundColor: color.surface, borderRadius: radius.md, borderWidth: 1, borderColor: color.border, padding: space.lg, gap: space.sm,
  },
  toast: {
    position: 'absolute', left: space.lg, right: space.lg, bottom: 96, padding: space.lg, borderRadius: radius.md, ...shadow,
  },
  backdrop: { flex: 1, backgroundColor: 'rgba(20,35,43,0.4)', justifyContent: 'center', padding: space.xxl },
  dialog: { backgroundColor: color.surface, borderRadius: radius.lg, padding: space.xxl, gap: space.md, maxWidth: 480, width: '100%', alignSelf: 'center' },
  dialogButtons: { flexDirection: 'row', gap: space.md, marginTop: space.sm },
  offline: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: space.sm, backgroundColor: color.textMuted, paddingVertical: space.xs,
  },
});
