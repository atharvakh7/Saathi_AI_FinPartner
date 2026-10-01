/**
 * S38 Notification Settings (spec §4.7): each change is saved immediately (optimistic, rolled back
 * on error). Times are chosen from a list (every 30 min). The per-kind switches stay usable when push
 * is off: they also control the in-app notification list (push only decides whether the phone pings).
 * The OS permission prompt when push is first enabled comes with push registration in step 30.
 */
import { StyleSheet, View } from 'react-native';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';

import { getNotificationSettings, putNotificationSettings, type NotificationSettingsDTO } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import { Card, ErrorBanner, Screen, Select, SkeletonCard } from '@/components';
import { ToggleRow } from '@/features/settings/SettingsRow';
import { useUiStore } from '@/stores';
import { space } from '@/theme';

const KEY = ['notification-settings'];
const TIMES = Array.from({ length: 33 }, (_, i) => {
  const minutes = 6 * 60 + i * 30; // 06:00 … 22:00
  return `${String(Math.floor(minutes / 60)).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}`;
});
const hhmm = (v: string) => v.slice(0, 5);

type BoolKey = { [K in keyof NotificationSettingsDTO]: NotificationSettingsDTO[K] extends boolean ? K : never }[keyof NotificationSettingsDTO];

export default function NotificationSettings() {
  const { t } = useTranslation();
  const settings = useQuery({ queryKey: KEY, queryFn: getNotificationSettings });
  const save = useMutation({
    mutationFn: putNotificationSettings,
    onMutate: async (patch) => {
      await queryClient.cancelQueries({ queryKey: KEY });
      const before = queryClient.getQueryData<NotificationSettingsDTO>(KEY);
      if (before) queryClient.setQueryData(KEY, { ...before, ...patch });
      return { before };
    },
    onError: (_e, _p, ctx) => {
      if (ctx?.before) queryClient.setQueryData(KEY, ctx.before);
      useUiStore.getState().showToast(t('settings.notSaved'), 'error');
    },
    onSuccess: (data) => queryClient.setQueryData(KEY, data),
  });
  const s = settings.data;
  const toggle = (key: BoolKey, labelKey: string, hintKey?: string, disabled?: boolean) => (
    <ToggleRow key={key} label={t(labelKey)} hint={hintKey ? t(hintKey) : undefined} value={!!s?.[key]} disabled={disabled}
      onChange={(v) => save.mutate({ [key]: v })} />
  );
  const timeOptions = TIMES.map((v) => ({ value: v, label: v }));

  return (
    <Screen title={t('settings.notifications.title')} back>
      {settings.isPending ? <SkeletonCard lines={6} /> : null}
      {settings.error ? <ErrorBanner error={settings.error} onRetry={() => void settings.refetch()} /> : null}
      {s ? (
        <>
          <Card>{toggle('push_enabled', 'settings.notifications.push', 'settings.notifications.pushHint')}</Card>
          <Card>
            {toggle('daily_insight_enabled', 'settings.notifications.dailyInsight')}
            {s.daily_insight_enabled ? (
              <View style={styles.time}>
                <Select label={t('settings.notifications.at')} value={hhmm(s.daily_insight_time)} options={timeOptions}
                  onChange={(v) => save.mutate({ daily_insight_time: v })} />
              </View>
            ) : null}
            {toggle('income_reminder_enabled', 'settings.notifications.incomeReminder', 'settings.notifications.weekly')}
            {toggle('goal_reminder_enabled', 'settings.notifications.goalReminder')}
            {toggle('scheme_deadline_enabled', 'settings.notifications.schemeDeadline')}
            {toggle('lean_month_alert_enabled', 'settings.notifications.leanMonth')}
            {toggle('streak_reminder_enabled', 'settings.notifications.streak')}
            {s.streak_reminder_enabled ? (
              <View style={styles.time}>
                <Select label={t('settings.notifications.at')} value={hhmm(s.streak_reminder_time)} options={timeOptions}
                  onChange={(v) => save.mutate({ streak_reminder_time: v })} />
              </View>
            ) : null}
          </Card>
        </>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({ time: { paddingLeft: space.lg, paddingBottom: space.sm } });
