/**
 * Form rules for S15 (transaction) and S16 (debt), the same as the finance API. Pure functions so
 * they can be unit-tested; values are i18n keys.
 */
import type { DebtInput, TransactionInput } from '@/api/endpoints';
import {
  CATEGORIES_BY_TYPE, DEBT_TYPES, MAX_DEBT_AMOUNT, MAX_INTEREST_PCT, MAX_TX_AMOUNT, NOTE_MAX,
  type DebtType, type TxCategory, type TxType,
} from '@/lib/constants';

export type Errors<K extends string> = Partial<Record<K, string>>;

const hasAtMost2Decimals = (n: number) => Math.abs(Math.round(n * 100) - n * 100) < 1e-6;

export interface TxFormValues {
  type: TxType;
  amount: number | null;
  category: TxCategory | null;
  occurredOn: string; // YYYY-MM-DD
  note: string;
}

export function validateTransaction(v: TxFormValues, today: string): Errors<'amount' | 'category' | 'occurredOn' | 'note'> {
  const e: Errors<'amount' | 'category' | 'occurredOn' | 'note'> = {};
  if (v.amount === null || !(v.amount > 0)) e.amount = 'finance.form.amountRequired';
  else if (v.amount > MAX_TX_AMOUNT) e.amount = 'finance.form.amountTooLarge';
  else if (!hasAtMost2Decimals(v.amount)) e.amount = 'finance.form.amountRequired';
  if (!v.category) e.category = 'finance.form.categoryRequired';
  else if (!CATEGORIES_BY_TYPE[v.type].includes(v.category)) e.category = 'finance.form.categoryRequired';
  if (!/^\d{4}-\d{2}-\d{2}$/.test(v.occurredOn)) e.occurredOn = 'form.required';
  else if (v.occurredOn > today) e.occurredOn = 'finance.form.noFuture';
  if (v.note.trim().length > NOTE_MAX) e.note = 'form.tooLong';
  return e;
}

export function transactionBody(v: TxFormValues): TransactionInput {
  return {
    type: v.type,
    amount_inr: v.amount!,
    category: v.category!,
    occurred_on: v.occurredOn,
    note: v.note.trim() || null,
  };
}

export interface DebtFormValues {
  lender: string;
  debtType: DebtType | null;
  principal: number | null;
  rate: string; // "% per year", typed
  minPayment: number | null;
  dueDay: number | null;
}

type DebtField = 'lender' | 'debtType' | 'principal' | 'rate' | 'minPayment';

/** A new debt needs principal > 0 (S16); an existing one may be 0 once paid off. */
export function validateDebt(v: DebtFormValues, isNew: boolean): Errors<DebtField> {
  const e: Errors<DebtField> = {};
  const lender = v.lender.trim();
  if (lender.length < 2 || lender.length > 80) e.lender = 'finance.debt.lenderLength';
  if (!v.debtType || !DEBT_TYPES.includes(v.debtType)) e.debtType = 'form.required';
  if (v.principal === null || v.principal < 0 || (isNew && v.principal === 0)) e.principal = 'finance.form.amountRequired';
  else if (v.principal > MAX_DEBT_AMOUNT) e.principal = 'finance.form.amountTooLarge';
  const rate = v.rate.trim();
  if (rate !== '' && (!/^\d+(\.\d{1,2})?$/.test(rate) || Number(rate) > MAX_INTEREST_PCT)) e.rate = 'finance.debt.rateRange';
  if (v.minPayment !== null && v.minPayment > MAX_DEBT_AMOUNT) e.minPayment = 'finance.form.amountTooLarge';
  return e;
}

export function debtBody(v: DebtFormValues): DebtInput {
  return {
    lender_name: v.lender.trim(),
    debt_type: v.debtType!,
    principal_outstanding_inr: v.principal!,
    interest_rate_pct: v.rate.trim() === '' ? 0 : Number(v.rate.trim()),
    min_monthly_payment_inr: v.minPayment ?? 0,
    due_day_of_month: v.dueDay,
  };
}
