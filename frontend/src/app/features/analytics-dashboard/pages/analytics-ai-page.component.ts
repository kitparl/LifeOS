import { Component, OnInit, inject, signal } from '@angular/core';
import { AnalyticsDashboardService } from '../services/analytics-dashboard.service';
import { AiInsightsResponse } from '../models/analytics-dashboard.models';
import { WidgetFrameComponent } from '../widgets/widget-frame.component';

@Component({
  selector: 'app-analytics-ai-page',
  standalone: true,
  imports: [WidgetFrameComponent],
  template: `
    @if (loading()) {
      <p class="text-sm text-[var(--text-muted)]">Loading AI insights…</p>
    } @else if (error()) {
      <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
    } @else if (data()) {
      <div class="space-y-3">
        <p class="text-sm text-[var(--text-muted)]">
          AI-powered insights are architected but not implemented yet. The provider interface is ready for a
          future swap.
        </p>
        <div class="grid gap-3 sm:grid-cols-2">
          @for (block of blocks; track block.period) {
            <app-widget-frame [title]="block.title" hint="Coming Soon">
              <p class="text-sm text-[var(--text-muted)]">{{ block.message }}</p>
              @if (block.items.length) {
                <ul class="mt-2 list-disc pl-4 text-sm">
                  @for (item of block.items; track item) {
                    <li>{{ item }}</li>
                  }
                </ul>
              }
            </app-widget-frame>
          }
        </div>
      </div>
    }
  `,
})
export class AnalyticsAiPageComponent implements OnInit {
  private readonly api = inject(AnalyticsDashboardService);
  readonly data = signal<AiInsightsResponse | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  get blocks() {
    const d = this.data();
    if (!d) return [];
    return [d.daily, d.weekly, d.monthly, d.predictions];
  }

  ngOnInit(): void {
    this.api.ai().subscribe({
      next: (d) => {
        this.data.set(d);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load AI insights');
        this.loading.set(false);
      },
    });
  }
}
