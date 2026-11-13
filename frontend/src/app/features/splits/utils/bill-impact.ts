import { SplitExpense } from '../models/split.models';

/**
 * What one bill does to a member's balance: what they paid minus their own share.
 * Positive = they lent that much, negative = they borrowed it, null = not on the bill at all.
 */
export function billImpactPaise(expense: SplitExpense, memberId: string): number | null {
  const paid = expense.paid_by === memberId ? expense.amount_paise : 0;
  const share = expense.shares.find((s) => s.member_id === memberId)?.amount_paise;
  if (share === undefined && paid === 0) return null;
  return paid - (share ?? 0);
}

/** Equal splits differ by at most one paise (the remainder); anything else was typed by hand. */
export function isEqualSplit(expense: SplitExpense): boolean {
  const amounts = expense.shares.map((s) => s.amount_paise);
  return amounts.length > 0 && Math.max(...amounts) - Math.min(...amounts) <= 1;
}
