import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-progress-ring',
  standalone: true,
  template: `
    <div class="relative inline-flex items-center justify-center">
      <svg viewBox="0 0 36 36" class="h-20 w-20" role="img" [attr.aria-label]="title">
        <path
          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none"
          stroke="var(--surface-3)"
          stroke-width="3"
        />
        <path
          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          fill="none"
          stroke="var(--primary)"
          stroke-width="3"
          [attr.stroke-dasharray]="dash"
          stroke-linecap="round"
        />
      </svg>
      <span class="absolute text-sm font-semibold">{{ value }}{{ unit }}</span>
    </div>
  `,
})
export class ProgressRingComponent {
  @Input() value = 0;
  @Input() max = 100;
  @Input() unit = '%';
  @Input() title = 'Progress';

  get dash(): string {
    const pct = Math.min(Math.max((this.value / (this.max || 1)) * 100, 0), 100);
    return `${pct}, 100`;
  }
}
