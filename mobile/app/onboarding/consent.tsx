/**
 * S06 Consent (spec §4.7, DPDP Act 2023): plain-language notice, link to the full Privacy Notice,
 * two required checkboxes and one optional. Continue -> POST /me/consents.
 */
import { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { useMutation } from '@tanstack/react-query';
import { Check, ChevronRight } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { postConsents, type ConsentType } from '@/api/endpoints';
import { AppText, Button, Card, ErrorBanner, Mascot, Screen } from '@/components';
import { PRIVACY_VERSION } from '@/lib/constants';
import { nextOnboardingRoute } from '@/lib/session';
import { color, MIN_TOUCH, radius, space } from '@/theme';

const ITEMS: { type: ConsentType; required: boolean }[] = [
  { type: 'terms_privacy', required: true },
  { type: 'personalization', required: true },
  { type: 'push_notifications', required: false },
];

function Checkbox({ checked, label, required, onToggle }: { checked: boolean; label: string; required: boolean; onToggle: () => void }) {
  const { t } = useTranslation();
  return (
    <Pressable onPress={onToggle} accessibilityRole="checkbox" accessibilityState={{ checked }}
      accessibilityLabel={`${label}${required ? `, ${t('common.required')}` : ''}`} style={styles.check}>
      <View style={[styles.box, checked && styles.boxOn]}>{checked ? <Check color={color.onPrimary} size={16} /> : null}</View>
      <View style={styles.flex}>
        <AppText>{label}</AppText>
        <AppText variant="caption" muted>{required ? t('common.required') : t('common.optional')}</AppText>
      </View>
    </Pressable>
  );
}

export default function Consent() {
  const { t } = useTranslation();
  const [granted, setGranted] = useState<Record<ConsentType, boolean>>({
    terms_privacy: false, personalization: false, push_notifications: false,
  });
  const ready = ITEMS.every((i) => !i.required || granted[i.type]);
  const save = useMutation({
    mutationFn: () => postConsents(ITEMS.map((i) => ({ consent_type: i.type, granted: granted[i.type] })), PRIVACY_VERSION),
    onSuccess: async () => router.replace((await nextOnboardingRoute()) as never),
  });
  const bullets = ['collect', 'purpose', 'retention', 'rights'] as const;

  return (
    <Screen footer={<Button label={t('common.continue')} disabled={!ready} loading={save.isPending} onPress={() => save.mutate()} />}>
      <View style={styles.center}>
        <Mascot pose="thinking" size={110} variant="bust" />
        <AppText variant="h2" align="center">{t('onboarding.consent.title')}</AppText>
      </View>
      <Card>
        {bullets.map((b) => (
          <View key={b} style={styles.bullet}>
            <AppText variant="bodyMedium">{t(`onboarding.consent.${b}Title`)}</AppText>
            <AppText variant="small" muted>{t(`onboarding.consent.${b}`)}</AppText>
          </View>
        ))}
        <Pressable onPress={() => router.push('/onboarding/privacy')} accessibilityRole="link" style={styles.link}>
          <AppText tint={color.primary}>{t('onboarding.consent.readFull')}</AppText>
          <ChevronRight color={color.primary} size={18} />
        </Pressable>
      </Card>
      {ITEMS.map((i) => (
        <Checkbox key={i.type} checked={granted[i.type]} required={i.required} label={t(`onboarding.consent.item.${i.type}`)}
          onToggle={() => setGranted((g) => ({ ...g, [i.type]: !g[i.type] }))} />
      ))}
      {save.error ? <ErrorBanner error={save.error} onRetry={() => save.mutate()} /> : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  center: { alignItems: 'center', gap: space.sm },
  bullet: { gap: 2, marginBottom: space.sm },
  link: { flexDirection: 'row', alignItems: 'center', minHeight: MIN_TOUCH },
  check: { flexDirection: 'row', alignItems: 'center', gap: space.md, minHeight: MIN_TOUCH, paddingVertical: space.xs },
  box: { width: 26, height: 26, borderRadius: radius.sm / 1.5, borderWidth: 2, borderColor: color.textMuted, alignItems: 'center', justifyContent: 'center' },
  boxOn: { backgroundColor: color.primary, borderColor: color.primary },
});
