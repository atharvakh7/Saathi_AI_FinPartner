/**
 * Profile form shared by S07 (onboarding, 3 steps) and S36 (edit profile, one page):
 * zod schema with the same rules as PUT /me/profile, prefill from ProfileDTO, request body, and
 * the three field sections.
 */
import { useEffect, useMemo } from 'react';
import { StyleSheet, View } from 'react-native';
import { Controller, type Control, type FieldPath, type UseFormGetValues, type UseFormSetValue } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { z } from 'zod';

import type { ProfileInput } from '@/api/endpoints';
import type { ProfileDTO } from '@/api/types';
import { AmountInput, AppText, SegmentedTabs, Select, TextField } from '@/components';
import { AREA_TYPES, GENDERS, INCOME_PATTERNS, OCCUPATIONS, SOCIAL_CATEGORIES, STATE_CODES } from '@/lib/constants';
import { color, space } from '@/theme';

const intText = (min: number, max: number, required: boolean) =>
  z.string().trim().refine((v) => (v === '' ? !required : /^\d+$/.test(v) && +v >= min && +v <= max), 'form.range');

export const profileSchema = z.object({
  full_name: z.string().trim().min(2, 'form.nameLength').max(80, 'form.nameLength'),
  age_years: intText(18, 100, true),
  gender: z.enum(GENDERS).nullable(),
  state_code: z.enum(STATE_CODES, { message: 'form.required' }).nullable().refine((v) => v !== null, 'form.required'),
  district: z.string().trim().max(60, 'form.tooLong'),
  area_type: z.enum(AREA_TYPES).nullable().refine((v) => v !== null, 'form.required'),
  occupation_type: z.enum(OCCUPATIONS).nullable().refine((v) => v !== null, 'form.required'),
  income_pattern: z.enum(INCOME_PATTERNS).nullable().refine((v) => v !== null, 'form.required'),
  declared_monthly_income_min_inr: z.number().min(0).nullable(),
  declared_monthly_income_max_inr: z.number().min(0).nullable(),
  household_size: intText(1, 20, false),
  dependents_count: intText(0, 19, false),
  has_bank_account: z.boolean().nullable(),
  social_category: z.enum(SOCIAL_CATEGORIES).nullable(),
  is_land_owner: z.boolean().nullable(),
  land_holding_hectares: z.string().trim().refine((v) => v === '' || (/^\d+(\.\d{1,2})?$/.test(v) && +v <= 500), 'form.landRange'),
});

export type ProfileFormValues = z.input<typeof profileSchema>;

/** Field groups: S07 steps 1–3, and the sections of S36. */
export const SECTIONS: FieldPath<ProfileFormValues>[][] = [
  ['full_name', 'age_years', 'gender', 'state_code', 'district', 'area_type'],
  ['occupation_type', 'income_pattern', 'declared_monthly_income_min_inr', 'declared_monthly_income_max_inr', 'household_size', 'dependents_count'],
  ['has_bank_account', 'social_category', 'is_land_owner', 'land_holding_hectares'],
];

export const EMPTY_PROFILE: ProfileFormValues = {
  full_name: '', age_years: '', gender: null, state_code: null, district: '', area_type: null, occupation_type: null,
  income_pattern: null, declared_monthly_income_min_inr: null, declared_monthly_income_max_inr: null, household_size: '',
  dependents_count: '', has_bank_account: null, social_category: null, is_land_owner: null, land_holding_hectares: '',
};

/**
 * Rules across fields (same as the API). Checked explicitly by the screens: an object-level zod
 * refinement doesn't run reliably when only one section's fields are validated.
 */
export function crossFieldErrors(v: ProfileFormValues): Partial<Record<keyof ProfileFormValues, string>> {
  const out: Partial<Record<keyof ProfileFormValues, string>> = {};
  const lo = v.declared_monthly_income_min_inr;
  const hi = v.declared_monthly_income_max_inr;
  if (lo !== null && hi !== null && hi < lo) out.declared_monthly_income_max_inr = 'form.maxGteMin';
  if (v.household_size !== '' && v.dependents_count !== '' && +v.dependents_count > +v.household_size - 1) {
    out.dependents_count = 'form.dependents';
  }
  return out;
}

export function formFromProfile(p: ProfileDTO): ProfileFormValues {
  const s = (n: number | null | undefined) => (n === null || n === undefined ? '' : String(n));
  return {
    ...EMPTY_PROFILE,
    full_name: p.full_name ?? '', age_years: s(p.age_years),
    gender: (p.gender as ProfileFormValues['gender']) ?? null, state_code: (p.state_code as ProfileFormValues['state_code']) ?? null,
    district: p.district ?? '', area_type: (p.area_type as ProfileFormValues['area_type']) ?? null,
    occupation_type: (p.occupation_type as ProfileFormValues['occupation_type']) ?? null,
    income_pattern: (p.income_pattern as ProfileFormValues['income_pattern']) ?? null,
    declared_monthly_income_min_inr: p.declared_monthly_income_min_inr,
    declared_monthly_income_max_inr: p.declared_monthly_income_max_inr,
    household_size: s(p.household_size), dependents_count: s(p.dependents_count),
    has_bank_account: p.has_bank_account, social_category: (p.social_category as ProfileFormValues['social_category']) ?? null,
    is_land_owner: p.is_land_owner, land_holding_hectares: p.land_holding_hectares === null ? '' : String(p.land_holding_hectares),
  };
}

export function profileBody(v: ProfileFormValues): ProfileInput {
  const int = (s: string) => (s.trim() === '' ? null : Number(s));
  const farmer = v.occupation_type === 'farmer';
  const money = (n: number | null) => (n === null ? null : Math.round(n));
  return {
    full_name: v.full_name.trim(), age_years: int(v.age_years), gender: v.gender, state_code: v.state_code,
    district: v.district.trim() || null, area_type: v.area_type, occupation_type: v.occupation_type,
    income_pattern: v.income_pattern, declared_monthly_income_min_inr: money(v.declared_monthly_income_min_inr),
    declared_monthly_income_max_inr: money(v.declared_monthly_income_max_inr), household_size: int(v.household_size),
    dependents_count: int(v.dependents_count), has_bank_account: v.has_bank_account, social_category: v.social_category,
    is_land_owner: farmer ? v.is_land_owner : null,
    land_holding_hectares: farmer && v.is_land_owner && v.land_holding_hectares ? v.land_holding_hectares : null,
  };
}

/** Spec prefills (S07): students -> irregular income; senior citizens -> age 60 (editable). */
export function useOccupationPrefills(
  occupation: ProfileFormValues['occupation_type'],
  getValues: UseFormGetValues<ProfileFormValues>,
  setValue: UseFormSetValue<ProfileFormValues>,
) {
  useEffect(() => {
    if (occupation === 'student' && !getValues('income_pattern')) setValue('income_pattern', 'irregular');
    if (occupation === 'senior_citizen' && !getValues('age_years')) setValue('age_years', '60');
  }, [occupation, getValues, setValue]);
}

export function YesNo({ value, onChange }: { value: boolean | null; onChange: (v: boolean) => void }) {
  const { t } = useTranslation();
  return (
    <SegmentedTabs<'yes' | 'no' | ''>
      value={value === null ? '' : value ? 'yes' : 'no'}
      onChange={(v) => onChange(v === 'yes')}
      options={[{ value: 'yes', label: t('common.yes') }, { value: 'no', label: t('common.no') }]}
    />
  );
}

export function LabeledField({ label, error, children, helper }: {
  label: string; error?: string; children: React.ReactNode; helper?: string;
}) {
  const { t } = useTranslation();
  return (
    <View style={styles.field}>
      <AppText variant="small">{label}</AppText>
      {children}
      {error ? <AppText variant="caption" tint={color.danger}>{t(error)}</AppText>
        : helper ? <AppText variant="caption" muted>{helper}</AppText> : null}
    </View>
  );
}

/** One field group. `err` returns an i18n key for a field's error, if any. */
export function ProfileSection({ section, control, err, occupation, landOwner }: {
  section: 0 | 1 | 2;
  control: Control<ProfileFormValues>;
  err: (name: keyof ProfileFormValues) => string | undefined;
  occupation: ProfileFormValues['occupation_type'];
  landOwner: boolean | null;
}) {
  const { t } = useTranslation();
  const stateOptions = useMemo(
    () => STATE_CODES.map((c) => ({ value: c, label: t(`state.${c}`) })).sort((a, b) => a.label.localeCompare(b.label)),
    [t],
  );
  const e = (name: keyof ProfileFormValues) => (err(name) ? t(err(name)!) : null);

  if (section === 0) {
    return (
      <>
        <Controller control={control} name="full_name" render={({ field }) => (
          <TextField label={t('onboarding.profile.fullName')} value={field.value} onChangeText={field.onChange} onBlur={field.onBlur}
            autoComplete="name" textContentType="name" error={e('full_name')} />
        )} />
        <Controller control={control} name="age_years" render={({ field }) => (
          <TextField label={t('eligibility.field.age_years')} value={field.value} keyboardType="number-pad" maxLength={3}
            onChangeText={(v) => field.onChange(v.replace(/\D/g, ''))} onBlur={field.onBlur}
            error={err('age_years') ? t('form.ageRange') : null} />
        )} />
        <Controller control={control} name="gender" render={({ field }) => (
          <Select label={t('eligibility.field.gender')} value={field.value} onChange={field.onChange} placeholder={t('common.optional')}
            options={GENDERS.map((g) => ({ value: g, label: t(`options.gender.${g}`) }))} />
        )} />
        <Controller control={control} name="state_code" render={({ field }) => (
          <Select label={t('eligibility.field.state_code')} value={field.value} onChange={field.onChange}
            placeholder={t('onboarding.profile.choose')} options={stateOptions} error={e('state_code')} />
        )} />
        <Controller control={control} name="district" render={({ field }) => (
          <TextField label={t('onboarding.profile.district')} value={field.value} onChangeText={field.onChange} maxLength={60}
            helper={t('common.optional')} error={e('district')} />
        )} />
        <Controller control={control} name="area_type" render={({ field }) => (
          <LabeledField label={t('eligibility.field.area_type')} error={err('area_type')}>
            <SegmentedTabs value={field.value ?? ''} onChange={field.onChange}
              options={AREA_TYPES.map((a) => ({ value: a, label: t(`options.area.${a}`) }))} />
          </LabeledField>
        )} />
      </>
    );
  }
  if (section === 1) {
    return (
      <>
        <Controller control={control} name="occupation_type" render={({ field }) => (
          <Select label={t('eligibility.q.occupation_type')} value={field.value} onChange={field.onChange}
            placeholder={t('onboarding.profile.choose')} error={e('occupation_type')}
            options={OCCUPATIONS.map((o) => ({ value: o, label: t(`options.occupation.${o}`) }))} />
        )} />
        <Controller control={control} name="income_pattern" render={({ field }) => (
          <Select label={t('onboarding.profile.incomePattern')} value={field.value} onChange={field.onChange}
            placeholder={t('onboarding.profile.choose')} error={e('income_pattern')}
            options={INCOME_PATTERNS.map((p) => ({ value: p, label: t(`options.incomePattern.${p}`) }))} />
        )} />
        <AppText variant="small">{t('onboarding.profile.incomeRange')}</AppText>
        <View style={styles.row}>
          <Controller control={control} name="declared_monthly_income_min_inr" render={({ field }) => (
            <View style={styles.flex}>
              <AmountInput label={t('onboarding.profile.lowest')} value={field.value} onChange={field.onChange} />
            </View>
          )} />
          <Controller control={control} name="declared_monthly_income_max_inr" render={({ field }) => (
            <View style={styles.flex}>
              <AmountInput label={t('onboarding.profile.highest')} value={field.value} onChange={field.onChange}
                error={e('declared_monthly_income_max_inr')} />
            </View>
          )} />
        </View>
        <View style={styles.row}>
          <Controller control={control} name="household_size" render={({ field }) => (
            <View style={styles.flex}>
              <TextField label={t('onboarding.profile.householdSize')} value={field.value} keyboardType="number-pad" maxLength={2}
                onChangeText={(v) => field.onChange(v.replace(/\D/g, ''))} error={err('household_size') ? t('form.householdRange') : null} />
            </View>
          )} />
          <Controller control={control} name="dependents_count" render={({ field }) => (
            <View style={styles.flex}>
              <TextField label={t('onboarding.profile.dependents')} value={field.value} keyboardType="number-pad" maxLength={2}
                onChangeText={(v) => field.onChange(v.replace(/\D/g, ''))}
                error={err('dependents_count') ? t(err('dependents_count') === 'form.range' ? 'form.dependentsRange' : err('dependents_count')!) : null} />
            </View>
          )} />
        </View>
      </>
    );
  }
  return (
    <>
      <Controller control={control} name="has_bank_account" render={({ field }) => (
        <LabeledField label={t('eligibility.q.has_bank_account')}><YesNo value={field.value} onChange={field.onChange} /></LabeledField>
      )} />
      <Controller control={control} name="social_category" render={({ field }) => (
        <Select label={t('eligibility.field.social_category')} value={field.value} onChange={field.onChange}
          placeholder={t('common.optional')} options={SOCIAL_CATEGORIES.map((c) => ({ value: c, label: t(`options.social.${c}`) }))} />
      )} />
      <AppText variant="caption" muted>{t('onboarding.profile.socialHelper')}</AppText>
      {occupation === 'farmer' ? (
        <Controller control={control} name="is_land_owner" render={({ field }) => (
          <LabeledField label={t('eligibility.q.is_land_owner')}><YesNo value={field.value} onChange={field.onChange} /></LabeledField>
        )} />
      ) : null}
      {occupation === 'farmer' && landOwner ? (
        <Controller control={control} name="land_holding_hectares" render={({ field }) => (
          <TextField label={t('onboarding.profile.landHectares')} value={field.value} keyboardType="decimal-pad"
            onChangeText={(v) => field.onChange(v.replace(/[^\d.]/g, ''))} helper={t('onboarding.profile.landHelper')}
            error={e('land_holding_hectares')} />
        )} />
      ) : null}
    </>
  );
}

/** Lazily collected eligibility answers shown on S36 only once answered (spec S36). */
export const LAZY_BOOL_FIELDS = [
  'is_bpl_household', 'is_income_tax_payer', 'is_student', 'is_street_vendor', 'is_unorganised_worker',
  'is_traditional_artisan', 'has_pucca_house', 'has_girl_child_below_10', 'is_head_of_household', 'is_govt_employee',
] as const;
export type LazyBoolField = (typeof LAZY_BOOL_FIELDS)[number];

const styles = StyleSheet.create({
  flex: { flex: 1 },
  field: { gap: space.xs },
  row: { flexDirection: 'row', gap: space.md },
});
