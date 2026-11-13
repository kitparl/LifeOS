import { SplitExpense } from '../models/split.models';
import { billImpactPaise, isEqualSplit } from './bill-impact';

function bill(paidBy: string, shares: [string, number][]): SplitExpense {
  return {
    id: 'e-1',
    title: 'Dinner',
    amount_paise: shares.reduce((sum, [, paise]) => sum + paise, 0),
    paid_by: paidBy,
    created_by: paidBy,
    expense_date: '2026-11-13',
    created_at: '2026-11-13T10:00:00Z',
    shares: shares.map(([member_id, amount_paise]) => ({ member_id, amount_paise })),
  };
}

describe('Split bill impact', () => {
  const dinner = bill('a', [['a', 3334], ['b', 3333], ['c', 3333]]);

  it('the payer lent everything but their own share; others borrowed their share', () => {
    expect(billImpactPaise(dinner, 'a')).toBe(6666);
    expect(billImpactPaise(dinner, 'b')).toBe(-3333);
    expect(billImpactPaise(dinner, 'd')).toBeNull();
  });

  it('paying for someone else lends the whole bill', () => {
    expect(billImpactPaise(bill('a', [['b', 25000]]), 'a')).toBe(25000);
  });

  it('tells equal splits (remainder paise only) from hand-typed ones', () => {
    expect(isEqualSplit(dinner)).toBeTrue();
    expect(isEqualSplit(bill('a', [['a', 5000], ['b', 2500]]))).toBeFalse();
  });
});
