/**
 * S15 Add / Edit Transaction. Expense | Income, amount (₹, > 0, at most ₹1,00,00,000), category grid,
 * date (today by default, never in the future), optional note. When adding, "Tell me in words"
 * (POST /transactions/parse) fills the form for the user to check before saving. Edit mode
 * (`?id=`) also offers Delete.
 */
import { useState } from 'react';
import { router, useLocalSearchParams } from 'expo-router';
import { useMutation } from '@tanstack/react-query';
import { Sparkles, Trash2 } from 'lucide-react-native';
import { useTranslation } from 'react-i18next';

import { ApiError } from '@/api/client';
import { createTransaction, deleteTransaction, parseTransaction, updateTransaction } from '@/api/endpoints';
import {
  AmountInput, AppText, Button, Card, ConfirmDialog, DateField, EmptyState, ErrorBanner, Screen, SegmentedTabs, TextField,
} from '@/components';
import { CategoryGrid } from '@/features/finance/categories';
import { cachedTransaction, invalidateFinance } from '@/features/finance/queries';
import { transactionBody, validateTransaction, type TxFormValues } from '@/features/finance/validation';
import { apiDate } from '@/lib/format';
import { CATEGORIES_BY_TYPE, NOTE_MAX, type TxCategory, type TxType } from '@/lib/constants';
import { useUiStore } from '@/stores';
import { useLanguageStore } from '@/stores/language';
import { color } from '@/theme';

const SERVER_FIELDS: Record<string, keyof TxFormValues> = {
  amount_inr: 'amount', category: 'category', occurred_on: 'occurredOn', note: 'note',
};

export default function TransactionForm() {
  const { t } = useTranslation();
  const language = useLanguageStore((s) => s.language);
  const params = useLocalSearchParams<{ id?: string; type?: string }>();
  const existing = params.id ? cachedTransaction(params.id) : undefined;
  const today = apiDate(new Date());

  const [values, setValues] = useState<TxFormValues>(() => existing
    ? { type: existing.type, amount: existing.amount_inr, category: existing.category, occurredOn: existing.occurred_on, note: existing.note ?? '' }
    : { type: params.type === 'income' ? 'income' : 'expense', amount: null, category: null, occurredOn: today, note: '' });
  const [showErrors, setShowErrors] = useState(false);
  const [words, setWords] = useState('');
  const [filled, setFilled] = useState(0); // remounts AmountInput after "fill for me"
  const [confirmDelete, setConfirmDelete] = useState(false);
  const update = (patch: Partial<TxFormValues>) => setValues((v) => ({ ...v, ...patch }));

  const save = useMutation({
    mutationFn: () => (existing ? updateTransaction(existing.id, transactionBody(values)) : createTransaction(transactionBody(values))),
    onSuccess: () => {
      invalidateFinance();
      useUiStore.getState().showToast(t('finance.form.saved'), 'success');
      router.back();
    },
  });
  const remove = useMutation({
    mutationFn: () => deleteTransaction(existing!.id),
    onSuccess: () => {
      invalidateFinance();
      setConfirmDelete(false);
      useUiStore.getState().showToast(t('finance.form.deleted'), 'success');
      router.back();
    },
  });
  const parse = useMutation({
    mutationFn: () => parseTransaction(words.trim(), language),
    onSuccess: ({ draft }) => {
      const type: TxType = draft.type;
      const category = (CATEGORIES_BY_TYPE[type] as readonly string[]).includes(draft.category) ? (draft.category as TxCategory) : null;
      setValues((v) => ({
        type, amount: draft.amount_inr, category,
        occurredOn: draft.occurred_on <= today ? draft.occurred_on : today,
        note: draft.note ?? v.note,
      }));
      setFilled((n) => n + 1);
    },
  });

  if (params.id && !existing) {
    return (
      <Screen title={t('finance.form.editTitle')} back>
        <EmptyState pose="thinking" message={t('errors.NOT_FOUND')} actionLabel={t('common.back')}
          onAction={() => (router.canGoBack() ? router.back() : router.replace('/finance/transactions'))} />
      </Screen>
    );
  }

  const clientErrors = validateTransaction(values, today);
  const serverErrors: Partial<Record<keyof TxFormValues, string>> = {};
  if (save.error instanceof ApiError) {
    for (const [field, issue] of Object.entries(save.error.fieldErrors())) {
      const key = SERVER_FIELDS[field];
      if (key) serverErrors[key] = issue;
    }
  }
  const errorFor = (k: keyof TxFormValues) => {
    const key = showErrors ? clientErrors[k as keyof typeof clientErrors] : undefined;
    return key ? t(key) : serverErrors[k] ?? null;
  };
  const submit = () => {
    setShowErrors(true);
    if (Object.keys(clientErrors).length === 0) save.mutate();
  };

  return (
    <Screen title={existing ? t('finance.form.editTitle') : t('finance.form.addTitle')} back
      right={existing ? (
        <Button label={t('common.delete')} variant="ghost" size="sm" fullWidth={false}
          icon={<Trash2 color={color.danger} size={18} />} onPress={() => setConfirmDelete(true)} />
      ) : undefined}
      footer={<Button label={t('common.save')} loading={save.isPending} onPress={submit} />}>
      {!existing ? (
        <Card>
          <AppText variant="bodyMedium">{t('finance.parse.title')}</AppText>
          <TextField value={words} onChangeText={setWords} placeholder={t('finance.parse.placeholder')} maxLength={500}
            multiline returnKeyType="done" />
          <Button label={t('finance.parse.fill')} variant="secondary" size="sm" loading={parse.isPending}
            disabled={words.trim().length === 0} icon={<Sparkles color={color.primary} size={18} />}
            onPress={() => parse.mutate()} />
          {parse.isSuccess ? <AppText variant="small" tint={color.primary}>{t('finance.parse.check')}</AppText> : null}
          {parse.error ? (
            <ErrorBanner message={parse.error instanceof ApiError && parse.error.code === 'VALIDATION_ERROR'
              ? t('finance.parse.notUnderstood') : undefined} error={parse.error} />
          ) : null}
        </Card>
      ) : null}

      <SegmentedTabs<TxType> value={values.type} options={[
        { value: 'expense', label: t('finance.filter.expense') },
        { value: 'income', label: t('finance.filter.income') },
      ]} onChange={(type) => update({
        type, category: values.category && CATEGORIES_BY_TYPE[type].includes(values.category) ? values.category : null,
      })} />

      <AmountInput key={`amount-${filled}`} label={t('finance.form.amount')} value={values.amount}
        onChange={(amount) => update({ amount })} error={errorFor('amount')} />

      <CategoryGrid type={values.type} value={values.category} onChange={(category) => update({ category })}
        error={errorFor('category')} />

      <DateField label={t('finance.form.date')} value={values.occurredOn} max={today} quick
        onChange={(occurredOn) => update({ occurredOn })} error={errorFor('occurredOn')} />

      <TextField label={`${t('finance.form.note')} (${t('common.optional')})`} value={values.note} maxLength={NOTE_MAX}
        placeholder={t('finance.form.notePlaceholder')} onChangeText={(note) => update({ note })} error={errorFor('note')} />

      {save.error && Object.keys(serverErrors).length === 0 ? (
        <ErrorBanner error={save.error} onRetry={submit} />
      ) : null}

      <ConfirmDialog visible={confirmDelete} title={t('finance.form.deleteTitle')} message={t('finance.form.deleteMessage')}
        confirmLabel={t('common.delete')} danger loading={remove.isPending}
        onConfirm={() => remove.mutate()} onCancel={() => setConfirmDelete(false)}>
        {remove.error ? <ErrorBanner error={remove.error} /> : null}
      </ConfirmDialog>
    </Screen>
  );
}
