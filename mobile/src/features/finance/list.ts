/** S14 list shaping: day headers between rows. */
import type { TransactionDTO } from '@/api/endpoints';

export type ListItem = { kind: 'day'; date: string } | { kind: 'tx'; tx: TransactionDTO };

/** Flatten pages into day headers + rows (the API returns newest first). */
export function groupByDay(txs: TransactionDTO[]): ListItem[] {
  const out: ListItem[] = [];
  let last = '';
  for (const tx of txs) {
    if (tx.occurred_on !== last) {
      out.push({ kind: 'day', date: tx.occurred_on });
      last = tx.occurred_on;
    }
    out.push({ kind: 'tx', tx });
  }
  return out;
}
