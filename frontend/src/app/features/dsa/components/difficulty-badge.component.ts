import { Component, computed, input } from '@angular/core';
import { DIFFICULTY_LABELS, Difficulty, difficultyTone } from '../models/dsa.models';

@Component({
  selector: 'app-dsa-difficulty-badge',
  standalone: true,
  template: `<span [class]="'badge badge--' + tone()">{{ label() }}</span>`,
})
export class DifficultyBadgeComponent {
  readonly difficulty = input.required<Difficulty>();
  readonly tone = computed(() => difficultyTone(this.difficulty()));
  readonly label = computed(() => DIFFICULTY_LABELS[this.difficulty()]);
}
