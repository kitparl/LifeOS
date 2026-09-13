import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface FinanceListResult {
  items: Record<string, unknown>[];
  total: number;
}

@Injectable({ providedIn: 'root' })
export class FinanceService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/finance`;

  summary(): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(`${this.api}/summary`);
  }

  listTransactions(opts?: { limit?: number; offset?: number }): Observable<FinanceListResult> {
    let params = new HttpParams();
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http
      .get<Record<string, unknown>[]>(`${this.api}/transactions`, { params, observe: 'response' })
      .pipe(
        map((response: HttpResponse<Record<string, unknown>[]>) => ({
          items: response.body ?? [],
          total: Number(response.headers.get('X-Total-Count') ?? response.body?.length ?? 0),
        })),
      );
  }

  createTransaction(data: Record<string, unknown>): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`${this.api}/transactions`, data);
  }

  deleteTransaction(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/transactions/${id}`);
  }

  listBudgets(): Observable<Record<string, unknown>[]> {
    return this.http.get<Record<string, unknown>[]>(`${this.api}/budgets`);
  }

  upsertBudget(data: Record<string, unknown>): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`${this.api}/budgets`, data);
  }
}
