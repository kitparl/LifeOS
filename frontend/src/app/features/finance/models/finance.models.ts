export type ExpenseKind = 'soft' | 'hard';
export type LoanStatus = 'ACTIVE' | 'COMPLETED' | 'FORECLOSED';
export type EMIStatus = 'PENDING' | 'PAID' | 'CANCELLED';
export type PartPaymentImpact = 'REDUCE_TENURE' | 'REDUCE_EMI';
export type PeriodPreset = 'this_month' | 'last_month' | 'this_year' | 'custom';

export interface PeriodSelection {
  preset: PeriodPreset;
  start?: string;
  end?: string;
}

/** Period totals. Deliberately has no `net` — income is context, not a balance. */
export interface FinanceOverview {
  period_start: string;
  period_end: string;
  label: string;
  total_income: number;
  total_expenses: number;
  soft_expenses: number;
  hard_expenses: number;
  loan_emi_expenses: number;
  recurring_expenses: number;
  expense_count: number;
  income_count: number;
}

export interface Expense {
  id: string;
  title: string | null;
  amount: number;
  txn_date: string;
  expense_kind: ExpenseKind | null;
  category: string;
  notes: string | null;
  recurring_id: string | null;
  loan_id: string | null;
  loan_emi_id: string | null;
  created_at: string;
}

export interface ExpensePayload {
  title: string;
  amount: number;
  txn_date: string;
  expense_kind: ExpenseKind;
  category: string;
  notes: string | null;
}

export interface Income {
  id: string;
  title: string | null;
  amount: number;
  txn_date: string;
  category: string;
  is_recurring: boolean;
  notes: string | null;
  created_at: string;
}

export interface IncomePayload {
  title: string;
  amount: number;
  txn_date: string;
  category: string;
  is_recurring: boolean;
  notes: string | null;
}

export interface RecurringExpense {
  id: string;
  title: string;
  amount: number;
  expense_kind: ExpenseKind;
  category: string;
  frequency: string;
  start_date: string;
  end_date: string | null;
  day_of_month: number;
  is_active: boolean;
  notes: string | null;
  created_at: string;
}

export interface RecurringPayload {
  title: string;
  amount: number;
  expense_kind: ExpenseKind;
  category: string;
  start_date: string;
  end_date: string | null;
  day_of_month: number;
  notes: string | null;
}

/** Loan progress figures are derived from EMI records, never stored. */
export interface Loan {
  id: string;
  name: string;
  lender: string | null;
  principal_amount: number;
  emi_amount: number;
  interest_rate: number | null;
  start_date: string;
  emi_start_date: string;
  tenure_months: number;
  emi_day: number;
  status: LoanStatus;
  notes: string | null;
  foreclosed_at: string | null;
  foreclosure_amount: number | null;
  foreclosure_notes: string | null;
  created_at: string;
  emis_total: number;
  emis_paid: number;
  emis_remaining: number;
  next_due_date: string | null;
  next_emi_amount: number | null;
}

/** Exactly one of tenure_months / last_emi_date is required. */
export interface LoanPayload {
  name: string;
  lender: string | null;
  principal_amount: number;
  emi_amount: number;
  interest_rate: number | null;
  start_date: string;
  emi_start_date: string;
  tenure_months?: number | null;
  last_emi_date?: string | null;
  emi_day: number;
  notes: string | null;
}

export interface LoanEMI {
  id: string;
  loan_id: string;
  emi_number: number;
  due_date: string;
  amount: number;
  status: EMIStatus;
  paid_date: string | null;
  expense_id: string | null;
}

/** Standing monthly obligation — not an additional expense figure. */
export interface LoanSummary {
  active_loans: number;
  monthly_emi_total: number;
}

export interface LoanPartPayment {
  id: string;
  loan_id: string;
  payment_date: string;
  amount: number;
  notes: string | null;
  impact: PartPaymentImpact;
  resulting_emi_amount: number | null;
  resulting_tenure_months: number | null;
  created_at: string;
}

export interface LoanPartPaymentPayload {
  payment_date: string;
  amount: number;
  notes: string | null;
  impact: PartPaymentImpact;
  new_emi_amount?: number | null;
  new_tenure_months?: number | null;
}

export interface LoanForeclosurePayload {
  foreclosure_date: string;
  foreclosure_amount: number;
  notes: string | null;
}

export interface CategoryTotal {
  category: string;
  amount: number;
}

export interface ExpenseBreakdown {
  period_start: string;
  period_end: string;
  categories: CategoryTotal[];
  soft_total: number;
  hard_total: number;
}

export interface UpcomingItem {
  due_date: string;
  title: string;
  amount: number;
  source: 'loan_emi' | 'recurring';
  loan_id: string | null;
  loan_emi_id: string | null;
  recurring_id: string | null;
}

export interface CategoryOptions {
  expense: string[];
  income: string[];
}

export interface FinanceListResult<T> {
  items: T[];
  total: number;
}
