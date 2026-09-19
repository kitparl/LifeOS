import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { McQuestion } from '../games/question-builder';

/** One multiple-choice question. Presentational only — the parent owns scoring/session
 * state and just tells us which question to show. */
@Component({
  selector: 'app-game-mc-question',
  standalone: true,
  template: `
    <div class="panel space-y-3 text-sm">
      <p class="font-semibold">{{ question.prompt }}</p>
      <div class="grid gap-2 sm:grid-cols-2">
        @for (option of question.options; track option; let i = $index) {
          <button
            type="button"
            class="btn-secondary text-left"
            [class.!border-green-600]="answered && i === question.correctIndex"
            [class.!border-red-600]="answered && selected === i && i !== question.correctIndex"
            [disabled]="answered"
            (click)="choose(i)"
          >
            {{ option }}
          </button>
        }
      </div>
    </div>
  `,
})
export class GameMcQuestionComponent implements OnChanges {
  @Input({ required: true }) question!: McQuestion;
  @Output() readonly answer = new EventEmitter<boolean>();

  answered = false;
  selected: number | null = null;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['question']) {
      this.answered = false;
      this.selected = null;
    }
  }

  choose(index: number): void {
    if (this.answered) return;
    this.answered = true;
    this.selected = index;
    this.answer.emit(index === this.question.correctIndex);
  }
}
