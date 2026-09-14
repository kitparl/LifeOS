import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  CategoryOptions,
  Expense,
  ExpenseBreakdown,
  ExpenseKind,
  ExpensePayload,
  FinanceListResult,
  FinanceOverview,
  Income,
  IncomePayload,
  Loan,
  LoanEMI,
  LoanPayload,
  LoanSummary,
  PeriodSelection,
  RecurringExpense,
  RecurringPayload,
  UpcomingItem,
} from '../models/finance.models';

function periodParams(period: PeriodSelection): HttpParams {
  let params = new HttpParams().set('preset', period.preset);
  if (period.preset === 'custom') {
    if (period.start) params = params.set('start', period.start);
    if (period.end) params = params.set('end', period.end);
  }
  return params;
}

@Injectable({ providedIn: 'root' })
export class FinanceService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/finance`;

  // ---- Overview -------------------------------------------------------

  overview(period: PeriodSelection): Observable<FinanceOverview> {
    return this.http.get<FinanceOverview>(`${this.api}/overview`, { params: periodParams(period) });
  }

  breakdown(period: PeriodSelection): Observable<ExpenseBreakdown> {
    return this.http.get<ExpenseBreakdown>(`${this.api}/breakdown`, { params: periodParams(period) });
  }

  upcoming(days = 30): Observable<UpcomingItem[]> {
    return this.http.get<UpcomingItem[]>(`${this.api}/upcoming`, {
      params: new HttpParams().set('days', String(days)),
    });
  }

  // ---- Expenses -------------------------------------------------------

  listExpenses(
    period: PeriodSelection,
    opts?: { kind?: ExpenseKind | null; category?: string | null; limit?: number; offset?: number },
  ): Observable<FinanceListResult<Expense>> {
    let params = periodParams(period);
    if (opts?.kind) params = params.set('expense_kind', opts.kind);
    if (opts?.category) params = params.set('category', opts.category);
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http
      .get<Expense[]>(`${this.api}/expenses`, { params, observe: 'response' })
      .pipe(map((res) => this.toListResult(res)));
  }

  createExpense(data: ExpensePayload): Observable<Expense> {
    return this.http.post<Expense>(`${this.api}/expenses`, data);
  }

  updateExpense(id: string, data: Partial<ExpensePayload>): Observable<Expense> {
    return this.http.patch<Expense>(`${this.api}/expenses/${id}`, data);
  }

  deleteExpense(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/expenses/${id}`);
  }

  // ---- Income ---------------------------------------------------------

  listIncome(
    period: PeriodSelection,
    opts?: { limit?: number; offset?: number },
  ): Observable<FinanceListResult<Income>> {
    let params = periodParams(period);
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http
      .get<Income[]>(`${this.api}/income`, { params, observe: 'response' })
      .pipe(map((res) => this.toListResult(res)));
  }

  createIncome(data: IncomePayload): Observable<Income> {
    return this.http.post<Income>(`${this.api}/income`, data);
  }

  updateIncome(id: string, data: Partial<IncomePayload>): Observable<Income> {
    return this.http.patch<Income>(`${this.api}/income/${id}`, data);
  }

  deleteIncome(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/income/${id}`);
  }

  // ---- Categories -----------------------------------------------------

  categories(): Observable<CategoryOptions> {
    return this.http.get<CategoryOptions>(`${this.api}/categories`);
  }

  createCategory(name: string, txnType: 'expense' | 'income' = 'expense'): Observable<CategoryOptions> {
    return this.http.post<CategoryOptions>(`${this.api}/categories`, { name, txn_type: txnType });
  }

  // ---- Recurring ------------------------------------------------------

  listRecurring(): Observable<RecurringExpense[]> {
    return this.http.get<RecurringExpense[]>(`${this.api}/recurring`);
  }

  createRecurring(data: RecurringPayload): Observable<RecurringExpense> {
    return this.http.post<RecurringExpense>(`${this.api}/recurring`, data);
  }

  updateRecurring(id: string, data: Partial<RecurringPayload> & { is_active?: boolean }): Observable<RecurringExpense> {
    return this.http.patch<RecurringExpense>(`${this.api}/recurring/${id}`, data);
  }

  deleteRecurring(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/recurring/${id}`);
  }

  // ---- Loans ----------------------------------------------------------

  listLoans(status?: 'ACTIVE' | 'CLOSED'): Observable<Loan[]> {
    let params = new HttpParams();
    if (status) params = params.set('loan_status', status);
    return this.http.get<Loan[]>(`${this.api}/loans`, { params });
  }

  loanSummary(): Observable<LoanSummary> {
    return this.http.get<LoanSummary>(`${this.api}/loans/summary`);
  }

  createLoan(data: LoanPayload): Observable<Loan> {
    return this.http.post<Loan>(`${this.api}/loans`, data);
  }

  updateLoan(id: string, data: Partial<LoanPayload> & { status?: 'ACTIVE' | 'CLOSED' }): Observable<Loan> {
    return this.http.patch<Loan>(`${this.api}/loans/${id}`, data);
  }

  listEmis(loanId: string): Observable<LoanEMI[]> {
    return this.http.get<LoanEMI[]>(`${this.api}/loans/${loanId}/emis`);
  }

  payEmi(loanId: string, emiId: string): Observable<LoanEMI> {
    return this.http.post<LoanEMI>(`${this.api}/loans/${loanId}/emis/${emiId}/pay`, {});
  }

  private toListResult<T>(response: HttpResponse<T[]>): FinanceListResult<T> {
    return {
      items: response.body ?? [],
      total: Number(response.headers.get('X-Total-Count') ?? response.body?.length ?? 0),
    };
  }
}
