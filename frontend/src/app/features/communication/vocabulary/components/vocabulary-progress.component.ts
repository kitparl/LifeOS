import { Component, EventEmitter, OnInit, Output, inject, signal } from '@angular/core';
import { VocabularyProgress } from '../models/vocabulary.models';
import { VocabularyService } from '../services/vocabulary.service';

/** Progress dashboard (PRD §52). Denominator is always server-computed — never a
 * hard-coded 15,000 (PRD §7, §62 rule 17). */
@Component({
  selector: 'app-vocabulary-progress',
  standalone: true,
  template: `
    <div class="space-y-3">
      @if (error()) {
        <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
      }

      @if (data(); as d) {
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div class="panel text-sm">
            <p style="color: var(--text-muted)">Vocabulary Learned</p>
            <p class="text-lg font-semibold">{{ d.vocabulary_learned }} / {{ d.total_available_vocabulary }}</p>
          </div>
          <div class="panel text-sm">
            <p style="color: var(--text-muted)">Current Level</p>
            <p class="text-lg font-semibold">{{ d.current_level ?? '—' }}</p>
          </div>
          <div class="panel text-sm">
            <p style="color: var(--text-muted)">Today's Progress</p>
            <p class="text-lg font-semibold">{{ d.todays_progress_count }} / {{ d.todays_progress_total }}</p>
          </div>
          <button type="button" class="panel text-left text-sm" (click)="openBookmarks.emit()">
            <p style="color: var(--text-muted)">Bookmarks</p>
            <p class="text-lg font-semibold">{{ d.bookmarks_count }}</p>
          </button>
          <div class="panel text-sm">
            <p style="color: var(--text-muted)">Needs Revision</p>
            <p class="text-lg font-semibold">{{ d.needs_revision_count }}</p>
          </div>
          <div class="panel text-sm">
            <p style="color: var(--text-muted)">Current Streak</p>
            <p class="text-lg font-semibold">{{ d.current_streak_days }} {{ d.current_streak_days === 1 ? 'day' : 'days' }}</p>
          </div>
        </div>
      }
    </div>
  `,
})
export class VocabularyProgressComponent implements OnInit {
  private readonly vocabularyService = inject(VocabularyService);
  @Output() readonly openBookmarks = new EventEmitter<void>();

  readonly data = signal<VocabularyProgress | null>(null);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.vocabularyService.getProgress().subscribe({
      next: (res) => this.data.set(res),
      error: () => this.error.set('Could not load progress.'),
    });
  }
}
