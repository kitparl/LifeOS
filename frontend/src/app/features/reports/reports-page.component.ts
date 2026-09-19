import { Component, inject } from '@angular/core';
import { ReportsService } from './services/reports.service';

@Component({
  selector: 'app-reports-page',
  standalone: true,
  template: `
    <div class="space-y-4">
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
        <p class="text-sm" style="color: var(--text-muted)">Generating…</p>
      }
      @if (content) {
        <div class="panel text-sm whitespace-pre-wrap">{{ content }}</div>
      }
    </div>
  `,
})
export class ReportsPageComponent {
  private readonly reports = inject(ReportsService);
  loading = false;
  content = '';

  loadReport(period: string): void {
    this.loading = true;
    this.reports.getReport(period).subscribe({
      next: (r) => {
        const sections = r.sections ?? [];
        const ai = r.ai_summary;
        this.content =
          sections.map((s) => `${s.title}\n${s.body}`).join('\n\n') +
          (ai ? `\n\nAI Summary:\n${ai}` : '');
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }

  loadReview(type: string): void {
    this.loading = true;
    this.reports.createReview(type).subscribe({
      next: (r) => {
        this.content = r.content ?? '';
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}
