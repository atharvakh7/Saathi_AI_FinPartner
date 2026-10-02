/**
 * S16 Add / Edit Debt: lender, type, amount still to pay (> 0 when adding), interest % per year,
 * monthly payment, due day. Editing adds "Mark as paid off" (status closed, kept for the record;
 * it no longer counts on Home) or "Still paying" to reopen, and Delete.
 */
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { CircleCheck, Trash2 } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { createDebt, deleteDebt, listDebts, updateDebt, type DebtDTO } from '@/api/endpoints';
import {
  AmountInput, AppText, Button, ConfirmDialog, EmptyState, ErrorBanner, Screen, Select, SkeletonCard, TextField,
} from '@/components';
import { financeKeys, invalidateFinance } from '@/features/finance/queries';
import { debtBody, validateDebt, type DebtFormValues } from '@/features/finance/validation';
import { DEBT_TYPES, type DebtType } from '@/lib/constants';
import { useUiStore } from '@/stores';
import { color, space } from '@/theme';

const SERVER_FIELDS: Record<string, keyof DebtFormValues> = {
  lender_name: 'lender', debt_type: 'debtType', principal_outstanding_inr: 'principal',
  interest_rate_pct: 'rate', min_monthly_payment_inr: 'minPayment',
};

const fromDebt = (d: DebtDTO): DebtFormValues => ({
  lender: d.lender_name, debtType: d.debt_type, principal: d.principal_outstanding_inr,
  rate: d.interest_rate_pct ? String(d.interest_rate_pct) : '', minPayment: d.min_monthly_payment_inr || null,
  dueDay: d.due_day_of_month,
});

const EMPTY: DebtFormValues = { lender: '', debtType: null, principal: null, rate: '', minPayment: null, dueDay: null };

export default function DebtScreen() {
  const { t } = useTranslation();
  const { id } = useLocalSearchParams<{ id?: string }>();
  const debts = useQuery({ queryKey: financeKeys.debts, queryFn: listDebts, enabled: !!id });
  const existing = id ? debts.data?.find((d) => d.id === id) : undefined;

  if (id && debts.isPending) {
    return <Screen title={t('finance.debt.editTitle')} back><SkeletonCard lines={6} /></Screen>;
  }
  if (id && debts.error) {
    return <Screen title={t('finance.debt.editTitle')} back><ErrorBanner error={debts.error} onRetry={() => void debts.refetch()} /></Screen>;
  }
  if (id && !existing) {
    return (
      <Screen title={t('finance.debt.editTitle')} back>
        <EmptyState pose="thinking" message={t('errors.NOT_FOUND')} actionLabel={t('common.back')}
          onAction={() => (router.canGoBack() ? router.back() : router.replace('/finance/debts'))} />
      </Screen>
    );
  }
  return <DebtForm key={existing?.id ?? 'new'} existing={existing} />;
}

function DebtForm({ existing }: { existing?: DebtDTO }) {
  const { t } = useTranslation();
  const [values, setValues] = useState<DebtFormValues>(existing ? fromDebt(existing) : EMPTY);
  const [showErrors, setShowErrors] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const update = (patch: Partial<DebtFormValues>) => setValues((v) => ({ ...v, ...patch }));
  const done = (message: string) => {
    invalidateFinance();
    useUiStore.getState().showToast(message, 'success');
    router.back();
  };

  const save = useMutation({
    mutationFn: () => (existing ? updateDebt(existing.id, debtBody(values)) : createDebt(debtBody(values))),
    onSuccess: () => done(t('finance.form.saved')),
  });
  const setStatus = useMutation({
    mutationFn: (status: 'active' | 'closed') => updateDebt(existing!.id, { status }),
    onSuccess: (_d, status) => done(status === 'closed' ? t('finance.debt.markedPaid') : t('finance.form.saved')),
  });
  const remove = useMutation({
    mutationFn: () => deleteDebt(existing!.id),
    onSuccess: () => {
      setConfirmDelete(false);
      done(t('finance.form.deleted'));
    },
  });

  const clientErrors = validateDebt(values, !existing);
  const serverErrors: Partial<Record<keyof DebtFormValues, string>> = {};
  if (save.error instanceof ApiError) {
    for (const [field, issue] of Object.entries(save.error.fieldErrors())) {
      const key = SERVER_FIELDS[field];
      if (key) serverErrors[key] = issue;
    }
  }
  const errorFor = (k: keyof DebtFormValues) => {
    const key = showErrors ? clientErrors[k as keyof typeof clientErrors] : undefined;
    return key ? t(key) : serverErrors[k] ?? null;
  };
  const submit = () => {
    setShowErrors(true);
    if (Object.keys(clientErrors).length === 0) save.mutate();
  };
  const dueOptions = [
    { value: '0', label: t('finance.debt.noDueDay') },
    ...Array.from({ length: 31 }, (_, i) => ({ value: String(i + 1), label: String(i + 1) })),
  ];

  return (
    <Screen title={existing ? t('finance.debt.editTitle') : t('finance.debt.addTitle')} back
      right={existing ? (
        <Button label={t('common.delete')} variant="ghost" size="sm" fullWidth={false}
          icon={<Trash2 color={color.danger} size={18} />} onPress={() => setConfirmDelete(true)} />
      ) : undefined}
      footer={<Button label={t('common.save')} loading={save.isPending} onPress={submit} />}>
      <TextField label={t('finance.debt.lender')} placeholder={t('finance.debt.lenderPlaceholder')} value={values.lender}
        maxLength={80} onChangeText={(lender) => update({ lender })} error={errorFor('lender')} />
      <Select<DebtType> label={t('finance.debt.type')} value={values.debtType} placeholder={t('form.choose')}
        options={DEBT_TYPES.map((d) => ({ value: d, label: t(`debttype.${d}`) }))}
        onChange={(debtType) => update({ debtType })} error={errorFor('debtType')} />
      <AmountInput label={t('finance.debt.amountLeft')} value={values.principal}
        onChange={(principal) => update({ principal })} error={errorFor('principal')} />
      <View style={styles.row}>
        <View style={styles.flex}>
          <TextField label={`${t('finance.debt.rate')} (${t('common.optional')})`} value={values.rate} keyboardType="decimal-pad"
            maxLength={6} suffix={<AppText muted>%</AppText>} onChangeText={(rate) => update({ rate: rate.replace(/[^\d.]/g, '') })}
            helper={t('finance.debt.rateHint')} error={errorFor('rate')} />
        </View>
        <View style={styles.flex}>
          <Select label={t('finance.debt.dueDay')} value={String(values.dueDay ?? 0)} options={dueOptions}
            onChange={(v) => update({ dueDay: Number(v) || null })} />
        </View>
      </View>
      <AmountInput label={`${t('finance.debt.monthly')} (${t('common.optional')})`} value={values.minPayment}
        onChange={(minPayment) => update({ minPayment })} error={errorFor('minPayment')} />

      {save.error && Object.keys(serverErrors).length === 0 ? <ErrorBanner error={save.error} onRetry={submit} /> : null}

      {existing ? (
        <Button variant="secondary" loading={setStatus.isPending}
          label={existing.status === 'active' ? t('finance.debt.markPaid') : t('finance.debt.reopen')}
          icon={existing.status === 'active' ? <CircleCheck color={color.primary} size={18} /> : undefined}
          onPress={() => setStatus.mutate(existing.status === 'active' ? 'closed' : 'active')} />
      ) : null}
      {setStatus.error ? <ErrorBanner error={setStatus.error} /> : null}

      <ConfirmDialog visible={confirmDelete} title={t('finance.debt.deleteTitle')} message={t('finance.form.deleteMessage')}
        confirmLabel={t('common.delete')} danger loading={remove.isPending}
        onConfirm={() => remove.mutate()} onCancel={() => setConfirmDelete(false)}>
        {remove.error ? <ErrorBanner error={remove.error} /> : null}
      </ConfirmDialog>
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 },
  row: { flexDirection: 'row', gap: space.md, alignItems: 'flex-start' },
});
