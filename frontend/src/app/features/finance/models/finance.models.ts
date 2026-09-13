export interface FinanceSummary {
  total_income: number;
  total_expenses: number;
  net: number;
}

export interface FinanceTransaction {
  id: string;
  txn_type: 'income' | 'expense' | string;
  amount: number;
  category: string;
  txn_date: string;
  description: string | null;
}

export interface FinanceTransactionCreate {
  txn_type: string;
  amount: number;
  category: string;
  txn_date: string;
  description: string | null;
}

export interface FinanceListResult {
  items: FinanceTransaction[];
  total: number;
}
