/**
 * S39 Privacy & Data (spec §4.7, DPDP Act 2023): consent status (optional ones can be switched),
 * download my data (GET /me/export -> JSON file -> share sheet), delete my account (two steps:
 * confirm, then type DELETE -> DELETE /me), grievance contact.
 */
import { useState } from 'react';
import { Linking, Platform, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { File, Paths } from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import { useMutation, useQuery } from '@tanstack/react-query';
import { CircleCheck, Download, Mail, Trash2 } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { deleteAccount, exportMyData, getConsents, postConsents, type ConsentDTO, type ConsentType } from '@/api/endpoints';
import { queryClient } from '@/api/queryClient';
import { AppText, Button, Card, ConfirmDialog, ErrorBanner, Screen, SkeletonCard, TextField } from '@/components';
import { config } from '@/config';
import { ToggleRow } from '@/features/settings/SettingsRow';
import { PRIVACY_VERSION } from '@/lib/constants';
import { signOut } from '@/lib/session';
import { useUiStore } from '@/stores';
import { color, space } from '@/theme';

const KEY = ['consents'];
const REQUIRED: ConsentType[] = ['terms_privacy', 'personalization'];

async function saveExport(json: string): Promise<'shared' | 'downloaded'> {
  const name = `saathi-data-${new Date().toISOString().slice(0, 10)}.json`;
  if (Platform.OS === 'web') {
    const url = URL.createObjectURL(new Blob([json], { type: 'application/json' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
    return 'downloaded';
  }
  const file = new File(Paths.cache, name);
  if (file.exists) file.delete();
  file.create();
  file.write(json);
  if (await Sharing.isAvailableAsync()) {
    await Sharing.shareAsync(file.uri, { mimeType: 'application/json', dialogTitle: name, UTI: 'public.json' });
    return 'shared';
  }
  return 'downloaded';
}

export default function Privacy() {
  const { t } = useTranslation();
  const consents = useQuery({ queryKey: KEY, queryFn: getConsents });
  const granted = (type: ConsentType) => !!consents.data?.find((c) => c.consent_type === type)?.granted;
  const [step, setStep] = useState<0 | 1 | 2>(0); // delete flow: 0 closed, 1 confirm, 2 type DELETE
  const [typed, setTyped] = useState('');

  const setPush = useMutation({
    mutationFn: (value: boolean) => postConsents(
      (['terms_privacy', 'personalization', 'push_notifications'] as ConsentType[]).map((type) => ({
        consent_type: type, granted: type === 'push_notifications' ? value : granted(type),
      })),
      PRIVACY_VERSION,
    ),
    onSuccess: (data: ConsentDTO[]) => queryClient.setQueryData(KEY, data),
    onError: () => useUiStore.getState().showToast(t('settings.notSaved'), 'error'),
  });

  const download = useMutation({
    mutationFn: async () => saveExport(await exportMyData()),
    onSuccess: (how) => useUiStore.getState().showToast(t(how === 'shared' ? 'settings.privacy.exportShared' : 'settings.privacy.exportDone'), 'success'),
  });

  const remove = useMutation({
    mutationFn: deleteAccount,
    onSuccess: async () => {
      setStep(0);
      await signOut();
      router.replace('/onboarding/welcome');
      useUiStore.getState().showToast(t('settings.privacy.deleted'), 'info');
    },
  });

  return (
    <Screen title={t('settings.privacy.title')} back>
      <Card>
        <AppText variant="h3">{t('settings.privacy.consents')}</AppText>
        {consents.isPending ? <SkeletonCard lines={2} /> : null}
        {consents.error ? <ErrorBanner error={consents.error} onRetry={() => void consents.refetch()} /> : null}
        {consents.data ? (
          <>
            {REQUIRED.map((type) => (
              <View key={type} style={styles.status}>
                <CircleCheck color={granted(type) ? color.success : color.textMuted} size={20} />
                <View style={styles.flex}>
                  <AppText>{t(`onboarding.consent.item.${type}`)}</AppText>
                  <AppText variant="caption" muted>{t('settings.privacy.requiredHint')}</AppText>
                </View>
              </View>
            ))}
            <ToggleRow label={t('onboarding.consent.item.push_notifications')} value={granted('push_notifications')}
              disabled={setPush.isPending} onChange={(v) => setPush.mutate(v)} />
          </>
        ) : null}
        <Button label={t('onboarding.consent.readFull')} variant="ghost" onPress={() => router.push('/onboarding/privacy')} />
      </Card>

      <Card>
        <AppText variant="h3">{t('settings.privacy.yourData')}</AppText>
        <AppText variant="small" muted>{t('settings.privacy.exportHint')}</AppText>
        <Button label={t('settings.privacy.export')} variant="secondary" icon={<Download color={color.primary} size={18} />}
          loading={download.isPending} onPress={() => download.mutate()} />
        {download.error ? <ErrorBanner error={download.error} onRetry={() => download.mutate()} /> : null}
        <AppText variant="small" muted>{t('settings.privacy.deleteHint')}</AppText>
        <Button label={t('settings.privacy.delete')} variant="danger" icon={<Trash2 color={color.onPrimary} size={18} />}
          onPress={() => { setTyped(''); setStep(1); }} />
      </Card>

      <Card>
        <AppText variant="h3">{t('settings.privacy.grievance')}</AppText>
        <AppText variant="small" muted>{t('settings.privacy.grievanceHint')}</AppText>
        <Button label={config.grievanceEmail} variant="ghost" icon={<Mail color={color.primary} size={18} />}
          onPress={() => void Linking.openURL(`mailto:${config.grievanceEmail}`)} />
      </Card>

      <ConfirmDialog visible={step === 1} title={t('settings.privacy.deleteTitle')} message={t('settings.privacy.deleteWarning')}
        confirmLabel={t('common.continue')} danger onConfirm={() => setStep(2)} onCancel={() => setStep(0)} />
      <ConfirmDialog visible={step === 2} title={t('settings.privacy.typeDelete')}
        message={t('settings.privacy.typeDeleteHint')} confirmLabel={t('settings.privacy.deleteNow')} danger
        loading={remove.isPending} confirmDisabled={typed.trim() !== 'DELETE'}
        onConfirm={() => remove.mutate()}
        onCancel={() => setStep(0)}>
        <TextField label="DELETE" value={typed} onChangeText={setTyped} autoCapitalize="characters" autoCorrect={false}
          error={typed && typed.trim() !== 'DELETE' ? t('settings.privacy.typeExactly') : null} />
        {remove.error ? <ErrorBanner error={remove.error} /> : null}
      </ConfirmDialog>
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  status: { flexDirection: 'row', gap: space.md, alignItems: 'center', paddingVertical: space.sm },
});
