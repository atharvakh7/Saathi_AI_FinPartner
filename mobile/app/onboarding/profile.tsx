/**
 * S07 Profile Setup (spec §4.7): three steps with a progress bar, validated per step (same rules
 * as PUT /me/profile). Last step saves and continues to the assessment. Fields: src/features/profile.
 */
import { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { putProfile } from '@/api/endpoints';
import { AppText, Button, ErrorBanner, Screen } from '@/components';
import {
  crossFieldErrors, EMPTY_PROFILE, formFromProfile, profileBody, profileSchema, ProfileSection, SECTIONS,
  useOccupationPrefills, type ProfileFormValues,
} from '@/features/profile/form';
import { nextOnboardingRoute, useMe } from '@/lib/session';
import { color, radius, space } from '@/theme';

export default function Profile() {
  const { t } = useTranslation();
  const me = useMe();
  const [step, setStep] = useState(0);
  const { control, handleSubmit, trigger, watch, setValue, getValues, reset, setError, formState: { errors } } =
    useForm<ProfileFormValues>({ resolver: zodResolver(profileSchema), defaultValues: EMPTY_PROFILE, mode: 'onTouched' });

  // Resume: prefill from a partly saved profile.
  const profile = me.data?.profile;
  useEffect(() => {
    if (profile) reset(formFromProfile(profile));
  }, [profile, reset]);

  const occupation = watch('occupation_type');
  const landOwner = watch('is_land_owner');
  useOccupationPrefills(occupation, getValues, setValue);

  const save = useMutation({
    mutationFn: (v: ProfileFormValues) => putProfile(profileBody(v)),
    onSuccess: async () => router.replace((await nextOnboardingRoute()) as never),
  });
  const serverErrors = save.error instanceof ApiError ? save.error.fieldErrors() : {};
  const err = (name: keyof ProfileFormValues) => errors[name]?.message ?? (serverErrors[name] ? 'form.invalid' : undefined);
  const last = SECTIONS.length - 1;

  const next = async () => {
    if (!(await trigger(SECTIONS[step]))) return;
    const cross = Object.entries(crossFieldErrors(getValues()))
      .filter(([f]) => SECTIONS[step]!.includes(f as keyof ProfileFormValues) || step === last);
    if (cross.length) {
      for (const [field, message] of cross) setError(field as keyof ProfileFormValues, { type: 'custom', message });
      if (step === last) setStep(1); // they live on step 2
      return;
    }
    if (step < last) setStep(step + 1);
    else await handleSubmit((v) => save.mutate(v))();
  };

  return (
    <Screen
      back={step > 0 ? () => setStep(step - 1) : undefined}
      title={t('onboarding.profile.title')}
      footer={
        <View style={styles.buttons}>
          {step > 0 ? <Button label={t('common.back')} variant="secondary" style={styles.flex} onPress={() => setStep(step - 1)} /> : null}
          <Button label={step === last ? t('onboarding.profile.saveContinue') : t('common.next')}
            loading={save.isPending} style={styles.flex} onPress={() => void next()} />
        </View>
      }>
      <View style={styles.progress} accessibilityRole="progressbar" accessibilityValue={{ min: 1, max: 3, now: step + 1 }}>
        {SECTIONS.map((_, i) => <View key={i} style={[styles.bar, i <= step && styles.barOn]} />)}
      </View>
      <AppText variant="h2">{t(`onboarding.profile.step${step + 1}`)}</AppText>
      <ProfileSection section={step as 0 | 1 | 2} control={control} err={err} occupation={occupation} landOwner={landOwner} />
      {save.error ? <ErrorBanner error={save.error} onRetry={() => void next()} /> : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  buttons: { flexDirection: 'row', gap: space.md },
  progress: { flexDirection: 'row', gap: space.xs },
  bar: { flex: 1, height: 6, borderRadius: radius.pill, backgroundColor: color.border },
  barOn: { backgroundColor: color.primary },
});
