/**
 * S36 Edit Profile (spec §4.7): every S07 field on one page, plus the scheme-eligibility answers
 * the user has already given (shown only once answered). Save -> PUT /me/profile; the API then
 * recomputes scheme matches and the plan.
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
import { queryClient } from '@/api/queryClient';
import type { ProfileDTO } from '@/api/types';
import { AmountInput, AppText, Button, Card, ErrorBanner, Screen, SkeletonCard } from '@/components';
import {
  crossFieldErrors, EMPTY_PROFILE, formFromProfile, LabeledField, LAZY_BOOL_FIELDS, profileBody, profileSchema,
  ProfileSection, useOccupationPrefills, YesNo, type LazyBoolField, type ProfileFormValues,
} from '@/features/profile/form';
import { ME_KEY, useMe } from '@/lib/session';
import { useUiStore } from '@/stores';
import { space } from '@/theme';

type Lazy = Partial<Record<LazyBoolField, boolean>> & { annual_household_income_inr?: number | null };

function answeredLazy(p: ProfileDTO): Lazy {
  const out: Lazy = {};
  for (const f of LAZY_BOOL_FIELDS) if (p[f] !== null && p[f] !== undefined) out[f] = p[f] as boolean;
  if (p.annual_household_income_inr !== null) out.annual_household_income_inr = p.annual_household_income_inr;
  return out;
}

export default function EditProfile() {
  const { t } = useTranslation();
  const me = useMe();
  const profile = me.data?.profile;
  const [lazy, setLazy] = useState<Lazy>({});
  const { control, handleSubmit, trigger, watch, setValue, getValues, reset, setError, formState: { errors } } =
    useForm<ProfileFormValues>({ resolver: zodResolver(profileSchema), defaultValues: EMPTY_PROFILE, mode: 'onTouched' });

  useEffect(() => {
    if (!profile) return;
    reset(formFromProfile(profile));
    setLazy(answeredLazy(profile));
  }, [profile, reset]);

  const occupation = watch('occupation_type');
  const landOwner = watch('is_land_owner');
  useOccupationPrefills(occupation, getValues, setValue);

  const save = useMutation({
    mutationFn: (v: ProfileFormValues) => putProfile({ ...profileBody(v), ...lazy }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ME_KEY });
      await queryClient.invalidateQueries({ queryKey: ['schemes'] }); // matches are recomputed by the API
      useUiStore.getState().showToast(t('settings.saved'), 'success');
      router.back();
    },
  });
  const serverErrors = save.error instanceof ApiError ? save.error.fieldErrors() : {};
  const err = (name: keyof ProfileFormValues) => errors[name]?.message ?? (serverErrors[name] ? 'form.invalid' : undefined);

  const submit = async () => {
    if (!(await trigger())) return;
    const cross = Object.entries(crossFieldErrors(getValues()));
    if (cross.length) {
      for (const [f, m] of cross) setError(f as keyof ProfileFormValues, { type: 'custom', message: m });
      return;
    }
    await handleSubmit((v) => save.mutate(v))();
  };

  const lazyKeys = LAZY_BOOL_FIELDS.filter((f) => lazy[f] !== undefined);
  return (
    <Screen title={t('settings.editProfile')} back
      footer={<Button label={t('common.save')} loading={save.isPending} onPress={() => void submit()} />}>
      {me.isPending ? <SkeletonCard lines={6} /> : null}
      {me.error ? <ErrorBanner error={me.error} onRetry={() => void me.refetch()} /> : null}
      {profile ? (
        <>
          {([0, 1, 2] as const).map((section) => (
            <Card key={section}>
              <AppText variant="h3">{t(`onboarding.profile.step${section + 1}`)}</AppText>
              <View style={styles.fields}>
                <ProfileSection section={section} control={control} err={err} occupation={occupation} landOwner={landOwner} />
              </View>
            </Card>
          ))}
          {lazyKeys.length || lazy.annual_household_income_inr !== undefined ? (
            <Card>
              <AppText variant="h3">{t('settings.eligibilityAnswers')}</AppText>
              <AppText variant="caption" muted>{t('onboarding.profile.socialHelper')}</AppText>
              <View style={styles.fields}>
                {lazy.annual_household_income_inr !== undefined ? (
                  <AmountInput label={t('eligibility.field.annual_household_income_inr')} value={lazy.annual_household_income_inr ?? null}
                    onChange={(v) => setLazy((s) => ({ ...s, annual_household_income_inr: v === null ? null : Math.round(v) }))} />
                ) : null}
                {lazyKeys.map((f) => (
                  <LabeledField key={f} label={t(`eligibility.q.${f}`)}>
                    <YesNo value={lazy[f] ?? null} onChange={(v) => setLazy((s) => ({ ...s, [f]: v }))} />
                  </LabeledField>
                ))}
              </View>
            </Card>
          ) : null}
        </>
      ) : null}
      {save.error ? <ErrorBanner error={save.error} onRetry={() => void submit()} /> : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  fields: { gap: space.lg, marginTop: space.sm },
});
