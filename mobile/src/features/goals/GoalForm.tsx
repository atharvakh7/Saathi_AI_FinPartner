/**
 * S19 Create / Edit Goal. Create: pick a category tile (from /goals/templates), name (pre-filled with
 * the category name), target (Emergency Fund pre-filled with the planner's suggestion), optional
 * target date, money already saved. Edit: name, target, target date (can be cleared).
 */
import { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { createGoal, getEmergencyFund, getGoalTemplates, updateGoal, type GoalDTO } from '@/api/endpoints';
import { AmountInput, AppText, Button, DateField, ErrorBanner, Screen, SkeletonCard, TextField } from '@/components';
import { ToggleRow } from '@/features/settings/SettingsRow';
import { apiDate, inr } from '@/lib/format';
import { useUiStore } from '@/stores';
import { color, radius, shadow, space } from '@/theme';
import { GoalIcon } from './GoalCard';
import { goalKeys, invalidateGoals, validateGoal, type GoalFormValues } from './goals';

const inMonths = (n: number) => {
  const d = new Date();
  return apiDate(new Date(d.getFullYear(), d.getMonth() + n, d.getDate()));
};

export function GoalForm({ existing }: { existing?: GoalDTO }) {
  const { t } = useTranslation();
  const today = apiDate(new Date());
  const now = new Date();
  const tomorrow = apiDate(new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1));
  const templates = useQuery({ queryKey: goalKeys.templates, queryFn: getGoalTemplates, staleTime: Infinity, enabled: !existing });
  const ef = useQuery({ queryKey: ['emergency'], queryFn: getEmergencyFund, enabled: !existing });
  const [values, setValues] = useState<GoalFormValues>(existing ? {
    category: existing.category, title: existing.title, target: existing.target_amount_inr,
    hasDate: !!existing.target_date, targetDate: existing.target_date ?? inMonths(12), saved: null,
  } : { category: null, title: '', target: null, hasDate: false, targetDate: inMonths(12), saved: null });
  const [targetKey, setTargetKey] = useState(0); // remount AmountInput when a template fills it
  const [showErrors, setShowErrors] = useState(false);
  const update = (patch: Partial<GoalFormValues>) => setValues((v) => ({ ...v, ...patch }));

  const pick = (category: string) => {
    const efSuggestion = ef.data && ef.data.target_amount_inr > 0 ? Math.round(ef.data.target_amount_inr) : null;
    const wasDefaultTitle = !values.title || (values.category && values.title === t(`goalcat.${values.category}`));
    update({
      category,
      title: wasDefaultTitle ? (category === 'custom' ? '' : t(`goalcat.${category}`)) : values.title,
      target: category === 'emergency_fund' && efSuggestion && !values.target ? efSuggestion : values.target,
    });
    setTargetKey((k) => k + 1);
  };

  const save = useMutation({
    mutationFn: async () => {
      const target_date = values.hasDate ? values.targetDate : null;
      if (existing) {
        return updateGoal(existing.id, { title: values.title.trim(), target_amount_inr: values.target!, target_date });
      }
      return createGoal({
        title: values.title.trim(), category: values.category!, target_amount_inr: values.target!, target_date,
        ...(values.saved ? { current_amount_inr: values.saved } : {}),
      });
    },
    onSuccess: (goal) => {
      invalidateGoals();
      useUiStore.getState().showToast(t('finance.form.saved'), 'success');
      if (existing) router.back();
      else router.replace(`/goals/${goal.id}`);
    },
  });

  const errors = validateGoal(values, today);
  const err = (k: keyof typeof errors) => (showErrors && errors[k] ? t(errors[k]!) : null);
  const submit = () => {
    setShowErrors(true);
    if (Object.keys(errors).length === 0) save.mutate();
  };
  const efSuggestion = ef.data && ef.data.target_amount_inr > 0 ? Math.round(ef.data.target_amount_inr) : null;

  return (
    <Screen title={existing ? t('goals.editTitle') : t('goals.new')} back
      footer={<Button label={existing ? t('common.save') : t('goals.create')} loading={save.isPending} onPress={submit} />}>
      {!existing ? (
        <View style={styles.wrap}>
          <AppText variant="small">{t('goals.form.whatFor')}</AppText>
          {templates.isPending ? <SkeletonCard lines={3} /> : null}
          {templates.error ? <ErrorBanner error={templates.error} onRetry={() => void templates.refetch()} /> : null}
          <View style={styles.grid} accessibilityRole="radiogroup">
            {(templates.data ?? []).map((tpl) => {
              const on = values.category === tpl.category;
              return (
                <Pressable key={tpl.slug} onPress={() => pick(tpl.category)} accessibilityRole="radio"
                  accessibilityState={{ checked: on }} style={[styles.tile, on && styles.tileOn]}>
                  <GoalIcon category={tpl.category} size={36} />
                  <AppText variant="caption" align="center" numberOfLines={2}>{t(`goalcat.${tpl.category}`)}</AppText>
                </Pressable>
              );
            })}
          </View>
          {err('category') ? <AppText variant="caption" tint={color.danger}>{err('category')}</AppText> : null}
        </View>
      ) : null}

      <TextField label={t('goals.form.name')} value={values.title} maxLength={80} placeholder={t('goals.form.namePlaceholder')}
        onChangeText={(title) => update({ title })} error={err('title')} />
      <AmountInput key={`target-${targetKey}`} label={t('onboarding.goals.target')} value={values.target}
        onChange={(target) => update({ target })} error={err('target')}
        helper={values.category === 'emergency_fund' && efSuggestion ? t('onboarding.goals.efSuggestion', { amount: inr(efSuggestion) }) : undefined} />
      <View style={styles.wrap}>
        <ToggleRow label={t('goals.form.hasDate')} value={values.hasDate} onChange={(hasDate) => update({ hasDate })} />
        {values.hasDate ? (
          <DateField label={t('onboarding.goals.byWhen')} value={values.targetDate} min={tomorrow}
            onChange={(targetDate) => update({ targetDate })} error={err('targetDate')} />
        ) : null}
      </View>
      {!existing ? (
        <AmountInput label={`${t('goals.form.alreadySaved')} (${t('common.optional')})`} value={values.saved}
          onChange={(saved) => update({ saved })} error={err('saved')} />
      ) : null}
      {save.error ? (
        <ErrorBanner error={save.error} message={save.error instanceof ApiError && save.error.code === 'CONFLICT' ? save.error.message : undefined} />
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: space.sm },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
  tile: {
    width: '31%', flexGrow: 1, minHeight: 92, padding: space.sm, gap: space.xs, borderRadius: radius.md, borderWidth: 1.5,
    borderColor: 'transparent', backgroundColor: color.surface, alignItems: 'center', justifyContent: 'center', ...shadow,
  },
  tileOn: { borderColor: color.primary, backgroundColor: color.primaryTint },
});
