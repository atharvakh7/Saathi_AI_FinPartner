import type { TransactionDTO } from '@/api/endpoints';
import { groupByDay } from '@/features/finance/list';
import { debtBody, transactionBody, validateDebt, validateTransaction, type DebtFormValues, type TxFormValues } from '@/features/finance/validation';
import { apiMonth, dayLabel, monthGrid, parseApiDate, shiftMonth } from '@/lib/format';

test('month helpers', () => {
  expect(apiMonth(new Date(2026, 0, 31))).toBe('2026-01');
  expect(shiftMonth('2026-01', -1)).toBe('2025-12');
  expect(shiftMonth('2026-12', 1)).toBe('2027-01');
  expect(shiftMonth('2026-09', -21)).toBe('2024-12');
  expect(parseApiDate('2026-03-05').getDate()).toBe(5);
});

test('day labels for list headers', () => {
  const now = new Date(2026, 9, 1, 10); // 1 Oct 2026
  expect(dayLabel('2026-10-01', now).key).toBe('common.today');
  expect(dayLabel('2026-09-30', now).key).toBe('common.yesterday'); // across a month boundary
  expect(dayLabel('2026-09-29', now)).toEqual({ text: '29 Sep 2026' });
});

test('calendar grid starts on Sunday and pads weeks', () => {
  const grid = monthGrid('2026-10'); // 1 Oct 2026 is a Thursday
  expect(grid[0]).toEqual([null, null, null, null, '2026-10-01', '2026-10-02', '2026-10-03']);
  expect(grid.every((w) => w.length === 7)).toBe(true);
  expect(grid.flat().filter(Boolean)).toHaveLength(31);
  expect(monthGrid('2026-02').flat().filter(Boolean)).toHaveLength(28);
});

const tx = (v: Partial<TxFormValues> = {}): TxFormValues => ({
  type: 'expense', amount: 250, category: 'food', occurredOn: '2026-10-01', note: '', ...v,
});

test('transaction form rules match the API (S15)', () => {
  const today = '2026-10-01';
  expect(validateTransaction(tx(), today)).toEqual({});
  expect(validateTransaction(tx({ amount: null }), today).amount).toBe('finance.form.amountRequired');
  expect(validateTransaction(tx({ amount: 0 }), today).amount).toBe('finance.form.amountRequired');
  expect(validateTransaction(tx({ amount: 10_000_000 }), today)).toEqual({});
  expect(validateTransaction(tx({ amount: 10_000_000.01 }), today).amount).toBe('finance.form.amountTooLarge');
  expect(validateTransaction(tx({ amount: 1.005 }), today).amount).toBeDefined();
  expect(validateTransaction(tx({ category: 'salary' }), today).category).toBe('finance.form.categoryRequired'); // income cat on expense
  expect(validateTransaction(tx({ type: 'income', category: 'salary' }), today)).toEqual({});
  expect(validateTransaction(tx({ occurredOn: '2026-10-02' }), today).occurredOn).toBe('finance.form.noFuture');
  expect(validateTransaction(tx({ note: 'x'.repeat(201) }), today).note).toBe('form.tooLong');
  expect(transactionBody(tx({ note: '  ' })).note).toBeNull();
  expect(transactionBody(tx({ note: ' sabzi ' }))).toEqual({
    type: 'expense', amount_inr: 250, category: 'food', occurred_on: '2026-10-01', note: 'sabzi',
  });
});

const debt = (v: Partial<DebtFormValues> = {}): DebtFormValues => ({
  lender: 'SBI', debtType: 'bank_loan', principal: 50000, rate: '', minPayment: null, dueDay: null, ...v,
});

test('debt form rules match the API (S16)', () => {
  expect(validateDebt(debt(), true)).toEqual({});
  expect(validateDebt(debt({ lender: ' A ' }), true).lender).toBe('finance.debt.lenderLength');
  expect(validateDebt(debt({ debtType: null }), true).debtType).toBe('form.required');
  expect(validateDebt(debt({ principal: 0 }), true).principal).toBe('finance.form.amountRequired'); // new: must be > 0
  expect(validateDebt(debt({ principal: 0 }), false)).toEqual({}); // existing: may be paid down to 0
  expect(validateDebt(debt({ rate: '12.5' }), true)).toEqual({});
  expect(validateDebt(debt({ rate: '121' }), true).rate).toBe('finance.debt.rateRange');
  expect(validateDebt(debt({ rate: '1.234' }), true).rate).toBe('finance.debt.rateRange');
  expect(debtBody(debt({ rate: '', minPayment: null, dueDay: 5 }))).toEqual({
    lender_name: 'SBI', debt_type: 'bank_loan', principal_outstanding_inr: 50000, interest_rate_pct: 0,
    min_monthly_payment_inr: 0, due_day_of_month: 5,
  });
});

test('transactions are grouped under one header per day', () => {
  const row = (id: string, occurred_on: string): TransactionDTO => ({
    id, occurred_on, type: 'expense', amount_inr: 10, category: 'food', is_essential: true, note: null, source: 'manual',
    created_at: `${occurred_on}T10:00:00Z`,
  });
  const items = groupByDay([row('a', '2026-10-01'), row('b', '2026-10-01'), row('c', '2026-09-28')]);
  expect(items.map((i) => (i.kind === 'day' ? i.date : i.tx.id))).toEqual(['2026-10-01', 'a', 'b', '2026-09-28', 'c']);
});
