import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { DashboardSummary } from '../models/dashboard.models';

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly http = inject(HttpClient);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly summary = signal<DashboardSummary | null>(null);

  getSummary(): Observable<DashboardSummary> {
    this.loading.set(true);
    this.error.set(null);
    return this.http.get<DashboardSummary>(`${environment.apiUrl}/dashboard/summary`).pipe(
      tap({
        next: (data) => {
          this.summary.set(data);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('Failed to load dashboard');
          this.loading.set(false);
        },
      }),
    );
  }
}
