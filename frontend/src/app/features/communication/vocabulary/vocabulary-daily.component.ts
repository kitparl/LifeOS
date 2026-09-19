import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
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
  imports: [LucideDynamicIcon],
  template: `
    <div class="space-y-3">
      @if (error()) {
        <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
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
              <div
                class="panel text-sm space-y-1 cursor-pointer hover:bg-[var(--surface-2)]"
                role="link"
                tabindex="0"
                (click)="openDetail(item.vocabulary.id)"
                (keydown.enter)="openDetail(item.vocabulary.id)"
              >
                <div class="flex items-start justify-between gap-2">
                  <p class="font-semibold">{{ item.vocabulary.term }}</p>
                  <div class="flex shrink-0 items-center gap-1">
                    @if (item.was_changed) {
                      <span class="text-xs" style="color: var(--text-muted)">changed</span>
                    }
                    <button
                      type="button"
                      class="vocab-bookmark"
                      [class.vocab-bookmark--active]="item.is_bookmarked"
                      [disabled]="busy()"
                      [attr.aria-pressed]="item.is_bookmarked"
                      [attr.aria-label]="item.is_bookmarked ? 'Remove bookmark' : 'Bookmark'"
                      [title]="item.is_bookmarked ? 'Remove bookmark' : 'Bookmark'"
                      (click)="$event.stopPropagation(); toggleBookmark(item.vocabulary.id, item.is_bookmarked)"
                    >
                      <svg class="vocab-bookmark__icon" lucideIcon="bookmark" aria-hidden="true"></svg>
                    </button>
                  </div>
                </div>
                <p class="text-xs" style="color: var(--text-muted)">
                  {{ item.vocabulary.part_of_speech }} · {{ item.vocabulary.level }}
                </p>
                <p>{{ item.vocabulary.simple_meaning }}</p>
                <p class="text-xs italic" style="color: var(--text-muted)">{{ item.vocabulary.example }}</p>

                @if (d.current_set!.status === 'active') {
                  <div class="flex items-center gap-3 pt-1 text-xs">
                    <button
                      type="button"
                      class="underline"
                      [disabled]="busy()"
                      (click)="$event.stopPropagation(); change(item.position)"
                    >
                      Change
                    </button>
                  </div>
                }
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
  styles: `
    .vocab-bookmark {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 1.75rem;
      height: 1.75rem;
      margin: -0.25rem -0.25rem 0 0;
      padding: 0;
      border: none;
      border-radius: 3px;
      background: transparent;
      color: var(--text-muted);
      cursor: pointer;
    }
    .vocab-bookmark:hover:not(:disabled) {
      background: var(--surface-3);
      color: var(--text);
    }
    .vocab-bookmark--active {
      color: var(--primary);
    }
    .vocab-bookmark--active .vocab-bookmark__icon {
      fill: currentColor;
    }
    .vocab-bookmark:disabled {
      opacity: 0.55;
      cursor: default;
    }
    .vocab-bookmark__icon {
      width: 1rem;
      height: 1rem;
      stroke: currentColor;
    }
  `,
})
export class VocabularyDailyComponent implements OnInit {
  private readonly vocabularyService = inject(VocabularyService);
  private readonly router = inject(Router);

  readonly data = signal<DailySetResponse | null>(null);
  readonly error = signal<string | null>(null);
  readonly busy = signal(false);

  ngOnInit(): void {
    this.load();
  }

  openDetail(vocabularyId: string): void {
    this.router.navigate(['/communication/vocabulary', vocabularyId]);
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
      next: (updated) => {
        const current = this.data();
        if (current) this.data.set({ ...current, current_set: updated });
        this.busy.set(false);
      },
      error: () => {
        this.busy.set(false);
        this.error.set('Could not change that word — please try again.');
      },
    });
  }

  toggleBookmark(vocabularyId: string, currentlyBookmarked: boolean): void {
    this.setBookmarked(vocabularyId, !currentlyBookmarked);
    const onError = () => {
      this.setBookmarked(vocabularyId, currentlyBookmarked);
      this.error.set('Could not update the bookmark — please try again.');
    };
    if (currentlyBookmarked) {
      this.vocabularyService.removeBookmark(vocabularyId).subscribe({ error: onError });
    } else {
      this.vocabularyService.addBookmark(vocabularyId).subscribe({ error: onError });
    }
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

  private setBookmarked(vocabularyId: string, isBookmarked: boolean): void {
    const current = this.data();
    if (!current?.current_set) return;
    this.data.set({
      ...current,
      current_set: {
        ...current.current_set,
        items: current.current_set.items.map((item) =>
          item.vocabulary.id === vocabularyId ? { ...item, is_bookmarked: isBookmarked } : item,
        ),
      },
    });
  }
}
