import { Component, OnInit, inject } from '@angular/core';
import { PredictionItem, PredictionsService } from './services/predictions.service';

@Component({
  selector: 'app-predictions-page',
  standalone: true,
  template: `
    <div class="space-y-4">
      <h1 class="text-lg font-semibold">AI Predictions</h1>
      @if (items.length) {
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          @for (p of items; track p.key) {
            <div class="panel text-sm">
              <p class="text-gray-600">{{ p.label }}</p>
              <p class="text-2xl font-semibold">{{ p.score }}<span class="text-sm font-normal text-gray-500">/100</span></p>
              <p class="text-xs capitalize mt-1" [class]="levelClass(p.level)">{{ p.level }}</p>
              <p class="text-gray-700 mt-2">{{ p.summary }}</p>
            </div>
          }
        </div>
      } @else {
        <p class="text-sm text-gray-600">Loading predictions…</p>
      }
    </div>
  `,
})
export class PredictionsPageComponent implements OnInit {
  private readonly predictions = inject(PredictionsService);
  items: PredictionItem[] = [];

  ngOnInit(): void {
    this.predictions.summary().subscribe({
      next: (s) => {
        this.items = [
          s.running_readiness,
          s.burnout_risk,
          s.overspending_risk,
          s.learning_consistency,
          s.goal_completion_probability,
        ];
      },
    });
  }

  levelClass(level: string): string {
    if (level === 'high') return 'text-green-700';
    if (level === 'medium') return 'text-orange-700';
    return 'text-red-700';
  }
}
