import { Component, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-reports-page',
  standalone: true,
  template: `
    <div class="space-y-4">
      <h1 class="text-lg font-semibold">Reports & AI Reviews</h1>
      <div class="flex flex-wrap gap-2">
        <button type="button" class="btn-primary text-xs" (click)="loadReport('weekly')">Weekly report</button>
        <button type="button" class="btn-primary text-xs" (click)="loadReport('monthly')">Monthly report</button>
        <button type="button" class="btn-primary text-xs" (click)="loadReport('yearly')">Yearly report</button>
      </div>
      <div class="flex flex-wrap gap-2">
        <button type="button" class="input-field !w-auto text-xs" (click)="loadReview('daily')">Daily review</button>
        <button type="button" class="input-field !w-auto text-xs" (click)="loadReview('weekly')">Weekly review</button>
        <button type="button" class="input-field !w-auto text-xs" (click)="loadReview('monthly')">Monthly review</button>
      </div>
      @if (loading) {
        <p class="text-sm text-gray-600">Generating…</p>
      }
      @if (content) {
        <div class="panel text-sm whitespace-pre-wrap">{{ content }}</div>
      }
    </div>
  `,
})
export class ReportsPageComponent {
  private readonly http = inject(HttpClient);
  loading = false;
  content = '';

  loadReport(period: string): void {
    this.loading = true;
    this.http.get<Record<string, unknown>>(`${environment.apiUrl}/reports/${period}`).subscribe({
      next: (r) => {
        const sections = (r['sections'] as { title: string; body: string }[]) ?? [];
        const ai = r['ai_summary'] as string | null;
        this.content = sections.map((s) => `${s.title}\n${s.body}`).join('\n\n') + (ai ? `\n\nAI Summary:\n${ai}` : '');
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }

  loadReview(type: string): void {
    this.loading = true;
    this.http.post<Record<string, unknown>>(`${environment.apiUrl}/reports/reviews/${type}`, {}).subscribe({
      next: (r) => {
        this.content = (r['content'] as string) ?? '';
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}
