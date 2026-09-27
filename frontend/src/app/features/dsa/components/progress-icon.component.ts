import { Component, computed, input } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { ProgressStatus } from '../models/dsa.models';

const VIEW: Record<ProgressStatus, { icon: string; color: string; label: string }> = {
  solved: { icon: 'circle-check', color: 'var(--success)', label: 'Solved' },
  attempted: { icon: 'circle-dot', color: 'var(--warning)', label: 'Attempted' },
  not_started: { icon: 'circle', color: 'var(--text-faint)', label: 'Not started' },
};

@Component({
  selector: 'app-dsa-progress-icon',
  standalone: true,
  imports: [LucideDynamicIcon],
  template: `
    <svg
      class="h-4 w-4"
      [lucideIcon]="view().icon"
      [style.color]="view().color"
      role="img"
      [attr.aria-label]="view().label"
    ></svg>
  `,
})
export class ProgressIconComponent {
  readonly status = input.required<ProgressStatus>();
  readonly view = computed(() => VIEW[this.status()]);
}
