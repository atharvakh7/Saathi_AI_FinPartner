/**
 * S09 Goal Identification (spec §4.7): pick goals from the templates, give each a target and an
 * optional "by when"; Finish creates them one by one, then marks onboarding complete.
 * "By when" is a choice of horizons (6 months … 5 years) instead of a date picker — simpler for
 * first-time users (ASSUMPTIONS step 20). Emergency Fund is pre-filled with the planner's suggestion.
 */
import { useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Check } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { completeOnboarding, createGoal, getEmergencyFund, getGoalTemplates, type GoalTemplateDTO } from '@/api/endpoints';
import {
  AmountInput, AppText, Button, Card, ErrorBanner, MascotBubble, Screen, Select, SkeletonCard, TextField,
} from '@/components';
import { apiDate, inr } from '@/lib/format';
import { GOAL_HORIZONS } from '@/lib/constants';
import { refreshMe } from '@/lib/session';
import { useSessionStore } from '@/stores/session';
import { color, radius, space } from '@/theme';

interface Pick {
  amount: number | null;
  months: number | null;
  title: string; // only for "custom"
}

function addMonths(months: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() + months);
  return apiDate(d);
}

export default function Goals() {
  const { t } = useTranslation();
  const templates = useQuery({ queryKey: ['goals', 'templates'], queryFn: getGoalTemplates, staleTime: Infinity });
  const ef = useQuery({ queryKey: ['emergency'], queryFn: getEmergencyFund });
  const [picked, setPicked] = useState<Record<string, Pick>>({});
  const [showErrors, setShowErrors] = useState(false);
  const created = useRef(new Set<string>()); // so Retry doesn't create a goal twice

  const efSuggestion = ef.data && ef.data.target_amount_inr > 0 ? Math.round(ef.data.target_amount_inr) : null;
  const toggle = (tpl: GoalTemplateDTO) =>
    setPicked((p) => {
      const next = { ...p };
      if (next[tpl.slug]) delete next[tpl.slug];
      else next[tpl.slug] = {
        amount: tpl.category === 'emergency_fund' ? efSuggestion : tpl.default_target_inr, months: null, title: '',
      };
      return next;
    });

  const invalid = useMemo(() => Object.entries(picked).filter(([slug, p]) =>
    !p.amount || p.amount <= 0 || (slug === 'custom' && p.title.trim().length < 2)).map(([s]) => s), [picked]);

  const finish = useMutation({
    mutationFn: async () => {
      for (const tpl of templates.data ?? []) {
        const p = picked[tpl.slug];
        if (!p || created.current.has(tpl.slug)) continue;
        await createGoal({
          title: tpl.slug === 'custom' ? p.title.trim() : t(`goalcat.${tpl.category}`),
          category: tpl.category,
          target_amount_inr: p.amount!,
          target_date: p.months ? addMonths(p.months) : null,
        });
        created.current.add(tpl.slug);
      }
      return completeOnboarding();
    },
    onSuccess: async (user) => {
      useSessionStore.getState().setUser(user);
      await refreshMe(); // the tabs guard reads /me: it must already say onboarding is done
      router.replace('/home');
    },
  });
  const skip = useMutation({
    mutationFn: completeOnboarding,
    onSuccess: async (user) => {
      useSessionStore.getState().setUser(user);
      await refreshMe(); // the tabs guard reads /me: it must already say onboarding is done
      router.replace('/home');
    },
  });

  const horizonOptions = [
    { value: '0', label: t('onboarding.goals.noDate') },
    ...GOAL_HORIZONS.map((m) => ({
      value: String(m),
      label: m < 12 ? t('onboarding.goals.inMonths', { count: m }) : t('onboarding.goals.inYears', { count: m / 12 }),
    })),
  ];

  return (
    <Screen
      right={<Button label={t('onboarding.goals.skip')} variant="ghost" size="sm" fullWidth={false}
        loading={skip.isPending} onPress={() => skip.mutate()} />}
      footer={
        <Button label={t('onboarding.goals.finish')} loading={finish.isPending}
          disabled={Object.keys(picked).length === 0}
          onPress={() => { setShowErrors(true); if (invalid.length === 0) finish.mutate(); }} />
      }>
      <MascotBubble pose="point_up" text={t('onboarding.goals.bubble')} />
      {templates.isPending ? <SkeletonCard lines={6} /> : null}
      {templates.error ? <ErrorBanner error={templates.error} onRetry={() => void templates.refetch()} /> : null}
      <View style={styles.grid}>
        {(templates.data ?? []).map((tpl) => {
          const on = !!picked[tpl.slug];
          return (
            <Pressable key={tpl.slug} onPress={() => toggle(tpl)} accessibilityRole="checkbox" accessibilityState={{ checked: on }}
              style={[styles.tile, on && styles.tileOn]}>
              <AppText variant="small" tint={on ? color.onPrimary : color.text} align="center">{t(`goalcat.${tpl.category}`)}</AppText>
              {on ? <View style={styles.tick}><Check color={color.primary} size={12} /></View> : null}
            </Pressable>
          );
        })}
      </View>

      {(templates.data ?? []).filter((tpl) => picked[tpl.slug]).map((tpl) => {
        const p = picked[tpl.slug]!;
        const update = (patch: Partial<Pick>) => setPicked((s) => ({ ...s, [tpl.slug]: { ...s[tpl.slug]!, ...patch } }));
        const bad = showErrors && invalid.includes(tpl.slug);
        return (
          <Card key={tpl.slug}>
            <AppText variant="bodyMedium">{t(`goalcat.${tpl.category}`)}</AppText>
            {tpl.slug === 'custom' ? (
              <TextField label={t('onboarding.goals.customTitle')} value={p.title} maxLength={60}
                onChangeText={(v) => update({ title: v })} error={bad && p.title.trim().length < 2 ? t('form.nameLength') : null} />
            ) : null}
            <AmountInput label={t('onboarding.goals.target')} value={p.amount} onChange={(v) => update({ amount: v })}
              error={bad && (!p.amount || p.amount <= 0) ? t('onboarding.goals.targetRequired') : null}
              helper={tpl.category === 'emergency_fund' && efSuggestion ? t('onboarding.goals.efSuggestion', { amount: inr(efSuggestion) }) : undefined} />
            <Select label={t('onboarding.goals.byWhen')} value={String(p.months ?? 0)}
              onChange={(v) => update({ months: Number(v) || null })} options={horizonOptions} />
          </Card>
        );
      })}
      {finish.error ? <ErrorBanner error={finish.error} onRetry={() => finish.mutate()} /> : null}
      {skip.error ? <ErrorBanner error={skip.error} onRetry={() => skip.mutate()} /> : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm },
  tile: {
    width: '48%', flexGrow: 1, minHeight: 64, padding: space.md, borderRadius: radius.md, borderWidth: 1.5,
    borderColor: color.border, backgroundColor: color.surface, alignItems: 'center', justifyContent: 'center',
  },
  tileOn: { backgroundColor: color.primary, borderColor: color.primary },
  tick: {
    position: 'absolute', top: 6, right: 6, width: 18, height: 18, borderRadius: 9, backgroundColor: color.surface,
    alignItems: 'center', justifyContent: 'center',
  },
});
