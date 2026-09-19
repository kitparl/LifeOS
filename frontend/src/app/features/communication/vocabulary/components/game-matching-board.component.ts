import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { MatchPair } from '../games/question-builder';

interface Tile {
  key: string;
  text: string;
  vocabularyId: string;
  matched: boolean;
}

/** Click a term, then click its matching pair on the right. Wrong pairs record one
 * incorrect answer per attempt and simply deselect (PRD lists word/meaning matching as
 * revision-style games — no penalty state beyond scoring). */
@Component({
  selector: 'app-game-matching-board',
  standalone: true,
  template: `
    <div class="grid grid-cols-2 gap-3 text-sm">
      <div class="space-y-2">
        @for (tile of leftTiles; track tile.key) {
          <button
            type="button"
            class="btn-secondary w-full text-left"
            [class.!opacity-40]="tile.matched"
            [class.!border-[var(--primary)]]="selectedLeft === tile.key"
            [disabled]="tile.matched"
            (click)="selectLeft(tile.key)"
          >
            {{ tile.text }}
          </button>
        }
      </div>
      <div class="space-y-2">
        @for (tile of rightTiles; track tile.key) {
          <button
            type="button"
            class="btn-secondary w-full text-left"
            [class.!opacity-40]="tile.matched"
            [disabled]="tile.matched"
            (click)="selectRight(tile.key)"
          >
            {{ tile.text }}
          </button>
        }
      </div>
    </div>
  `,
})
export class GameMatchingBoardComponent implements OnChanges {
  @Input({ required: true }) pairs: MatchPair[] = [];
  @Output() readonly pairAnswered = new EventEmitter<{ vocabularyId: string; isCorrect: boolean }>();
  @Output() readonly allMatched = new EventEmitter<void>();

  leftTiles: Tile[] = [];
  rightTiles: Tile[] = [];
  selectedLeft: string | null = null;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['pairs']) {
      this.leftTiles = this.pairs.map((p) => ({ key: `L-${p.vocabularyId}`, text: p.left, vocabularyId: p.vocabularyId, matched: false }));
      this.rightTiles = shuffleTiles(
        this.pairs.map((p) => ({ key: `R-${p.vocabularyId}`, text: p.right, vocabularyId: p.vocabularyId, matched: false })),
      );
      this.selectedLeft = null;
    }
  }

  selectLeft(key: string): void {
    this.selectedLeft = key;
  }

  selectRight(rightKey: string): void {
    if (!this.selectedLeft) return;
    const left = this.leftTiles.find((t) => t.key === this.selectedLeft);
    const right = this.rightTiles.find((t) => t.key === rightKey);
    if (!left || !right) return;

    const isCorrect = left.vocabularyId === right.vocabularyId;
    if (isCorrect) {
      left.matched = true;
      right.matched = true;
    }
    this.pairAnswered.emit({ vocabularyId: left.vocabularyId, isCorrect });
    this.selectedLeft = null;

    if (this.leftTiles.every((t) => t.matched)) {
      this.allMatched.emit();
    }
  }
}

function shuffleTiles<T>(arr: T[]): T[] {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}
