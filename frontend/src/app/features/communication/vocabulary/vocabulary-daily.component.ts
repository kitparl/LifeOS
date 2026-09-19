import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DailySetResponse } from './models/vocabulary.models';
import { VocabularyService } from './services/vocabulary.service';

/**
 * Today's Words screen (PRD §48-49). The backend is the sole source of truth for
 * state/progression — this component only renders what `/vocabulary/today` returns
 * and triggers the accept/change/next-set actions; it never computes eligibility
 * itself (PRD §35).
 */
@Component({
  selector: 'app-vocabulary-daily',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="space-y-3">
      @if (error()) {
        <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
      }
      @if (bookmarkedId()) {
        <p class="text-xs" style="color: var(--text-muted)">Bookmarked "{{ bookmarkedId() }}".</p>
      }

      @if (data(); as d) {
        @if (d.current_set) {
          <div class="flex items-center justify-end">
            <p class="text-xs" style="color: var(--text-muted)">
              Progress: {{ d.progress_count }} / {{ d.progress_total }}
            </p>
          </div>

          <div class="grid gap-3 sm:grid-cols-2">
            @for (item of d.current_set.items; track item.position) {
              <div class="panel text-sm space-y-1">
                <div class="flex items-center justify-between">
                  <p class="font-semibold">{{ item.vocabulary.term }}</p>
                  @if (item.was_changed) {
                    <span class="text-xs" style="color: var(--text-muted)">changed</span>
                  }
                </div>
                <p class="text-xs" style="color: var(--text-muted)">
                  {{ item.vocabulary.part_of_speech }} · {{ item.vocabulary.level }}
                </p>
                <p>{{ item.vocabulary.simple_meaning }}</p>
                <p class="text-xs italic" style="color: var(--text-muted)">{{ item.vocabulary.example }}</p>

                <div class="flex items-center gap-3 pt-1 text-xs">
                  <button type="button" class="underline" [disabled]="busy()" (click)="bookmark(item.vocabulary.id)">
                    ♡ Bookmark
                  </button>
                  <a class="underline" [routerLink]="['/communication/vocabulary', item.vocabulary.id]">Details</a>
                  @if (d.current_set!.status === 'active') {
                    <button type="button" class="underline" [disabled]="busy()" (click)="change(item.position)">
                      Change
                    </button>
                  }
                </div>
              </div>
            }
          </div>

          <div class="flex flex-wrap gap-2 pt-1">
            @if (d.current_set.status === 'active') {
              <button type="button" class="btn-primary" [disabled]="busy()" (click)="accept(d.current_set!.id)">
                Accept Today's Words
              </button>
            } @else {
              <p class="text-sm" style="color: var(--text-muted)">
                Accepted. Your next daily set will be ready after 12:00 AM IST — or continue now:
              </p>
              <button type="button" class="btn-secondary" [disabled]="busy()" (click)="nextSet()">Next Set</button>
            }
          </div>
        } @else {
          <div class="panel text-sm">
            <p class="font-semibold">You've reached the end of the current vocabulary collection.</p>
            <p style="color: var(--text-muted)">
              There's no new vocabulary left to learn right now — check back after more is added.
            </p>
          </div>
        }
      }
    </div>
  `,
})
export class VocabularyDailyComponent implements OnInit {
  private readonly vocabularyService = inject(VocabularyService);

  readonly data = signal<DailySetResponse | null>(null);
  readonly error = signal<string | null>(null);
  readonly busy = signal(false);
  readonly bookmarkedId = signal<string | null>(null);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.vocabularyService.today().subscribe({
      next: (res) => this.data.set(res),
      error: () => this.error.set("Could not load today's vocabulary."),
    });
  }

  accept(setId: string): void {
    this.busy.set(true);
    this.vocabularyService.accept(setId).subscribe({
      next: () => {
        this.busy.set(false);
        this.load();
      },
      error: () => {
        this.busy.set(false);
        this.error.set('Could not accept the set — please try again.');
      },
    });
  }

  change(position: number): void {
    const setId = this.data()?.current_set?.id;
    if (!setId) return;
    this.busy.set(true);
    this.vocabularyService.changeItem(setId, position).subscribe({
      next: () => {
        this.busy.set(false);
        this.load();
      },
      error: () => {
        this.busy.set(false);
        this.error.set('Could not change that word — please try again.');
      },
    });
  }

  bookmark(vocabularyId: string): void {
    this.vocabularyService.addBookmark(vocabularyId).subscribe({
      next: () => this.bookmarkedId.set(vocabularyId),
      error: () => this.error.set('Could not bookmark that word — please try again.'),
    });
  }

  nextSet(): void {
    this.busy.set(true);
    this.vocabularyService.nextSet().subscribe({
      next: () => {
        this.busy.set(false);
        this.load();
      },
      error: () => {
        this.busy.set(false);
        this.error.set('Could not start the next set — please try again.');
      },
    });
  }
}
