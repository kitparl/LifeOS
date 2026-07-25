import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-chart-empty',
  standalone: true,
  template: `
    <div class="flex h-full min-h-[120px] items-center justify-center text-sm text-[var(--text-muted)]">
      {{ message }}
    </div>
  `,
})
export class ChartEmptyComponent {
  @Input() message = 'No data yet';
}
