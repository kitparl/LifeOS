import { Component, computed, input } from '@angular/core';
import { verdictTone } from '../models/dsa.models';

@Component({
  selector: 'app-dsa-verdict-badge',
  standalone: true,
  template: `<span [class]="'badge badge--' + tone()">{{ verdict() ?? 'Judging…' }}</span>`,
})
export class VerdictBadgeComponent {
  readonly verdict = input<string | null>(null);
  readonly tone = computed(() => verdictTone(this.verdict()));
}
