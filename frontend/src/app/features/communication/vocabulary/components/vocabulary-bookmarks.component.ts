import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { ListPaginatorComponent } from '../../../../shared/pagination/list-paginator.component';
import { BookmarkResponse } from '../models/vocabulary.models';
import { VocabularyService } from '../services/vocabulary.service';

const PAGE_SIZE = 20;

@Component({
  selector: 'app-vocabulary-bookmarks',
  standalone: true,
  imports: [ListPaginatorComponent, LucideDynamicIcon],
  template: `
    <div class="space-y-3">
      @if (error()) {
        <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
      }

      <div class="grid gap-2 sm:grid-cols-2">
        @for (item of items(); track item.id) {
          <div
            class="panel cursor-pointer text-left text-sm hover:bg-[var(--surface-2)]"
            role="link"
            tabindex="0"
            (click)="openDetail(item.vocabulary.id)"
            (keydown.enter)="openDetail(item.vocabulary.id)"
          >
            <div class="flex items-start justify-between gap-2">
              <p class="font-semibold">{{ item.vocabulary.term }}</p>
              <button
                type="button"
                class="vocab-bookmark vocab-bookmark--active"
                [disabled]="busyId() === item.vocabulary.id"
                aria-label="Remove bookmark"
                title="Remove bookmark"
                (click)="$event.stopPropagation(); remove(item)"
              >
                <svg class="vocab-bookmark__icon" lucideIcon="bookmark" aria-hidden="true"></svg>
              </button>
            </div>
            <p class="text-xs" style="color: var(--text-muted)">
              {{ item.vocabulary.part_of_speech }} · {{ item.vocabulary.level }}
            </p>
            <p>{{ item.vocabulary.simple_meaning }}</p>
          </div>
        }
      </div>

      @if (!items().length && !loading()) {
        <p class="text-sm" style="color: var(--text-muted)">
          No bookmarked words yet. Bookmark a word from Today's Words or a word's detail page.
        </p>
      }

      <app-list-paginator
        [total]="total()"
        [pageSize]="pageSize"
        [currentPage]="page()"
        (pageChange)="setPage($event)"
      />
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
      color: var(--primary);
      cursor: pointer;
    }
    .vocab-bookmark:hover:not(:disabled) {
      background: var(--surface-3);
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
export class VocabularyBookmarksComponent implements OnInit {
  private readonly vocabularyService = inject(VocabularyService);
  private readonly router = inject(Router);

  readonly pageSize = PAGE_SIZE;
  readonly items = signal<BookmarkResponse[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly error = signal<string | null>(null);
  readonly loading = signal(false);
  readonly busyId = signal<string | null>(null);

  ngOnInit(): void {
    this.load();
  }

  setPage(page: number): void {
    this.page.set(page);
    this.load();
  }

  openDetail(id: string): void {
    this.router.navigate(['/communication/vocabulary', id]);
  }

  remove(item: BookmarkResponse): void {
    this.busyId.set(item.vocabulary.id);
    this.vocabularyService.removeBookmark(item.vocabulary.id).subscribe({
      next: () => {
        this.busyId.set(null);
        const remaining = this.total() - 1;
        const lastPage = Math.max(1, Math.ceil(remaining / this.pageSize));
        if (this.page() > lastPage) this.page.set(lastPage);
        this.load();
      },
      error: () => {
        this.busyId.set(null);
        this.error.set('Could not remove that bookmark — please try again.');
      },
    });
  }

  load(): void {
    this.loading.set(true);
    const offset = (this.page() - 1) * this.pageSize;
    this.vocabularyService.getBookmarks(this.pageSize, offset).subscribe({
      next: (res) => {
        this.items.set(res.items);
        this.total.set(res.total);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Could not load bookmarks.');
        this.loading.set(false);
      },
    });
  }
}
