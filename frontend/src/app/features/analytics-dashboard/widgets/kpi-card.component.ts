import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-kpi-card',
  standalone: true,
  template: `
    <div class="panel text-sm">
      <p class="text-[var(--text-muted)]">{{ title }}</p>
      <p class="mt-1 text-xl font-semibold">
        {{ value }}@if (unit) {<span class="text-sm font-normal text-[var(--text-muted)]">{{ unit }}</span>}
      </p>
      @if (subtitle) {
        <p class="mt-0.5 text-xs text-[var(--text-faint)]">{{ subtitle }}</p>
      }
    </div>
  `,
})
export class KpiCardComponent {
  @Input({ required: true }) title!: string;
  @Input({ required: true }) value!: string | number;
  @Input() unit: string | null = null;
  @Input() subtitle: string | null = null;
}
