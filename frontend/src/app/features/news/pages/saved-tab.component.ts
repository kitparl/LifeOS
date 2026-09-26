import { Component, OnInit, inject, signal } from '@angular/core';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { ListPaginatorComponent } from '../../../shared/pagination/list-paginator.component';
import { PaginatedListState } from '../../../shared/pagination/paginated-list.state';
import { ArticleRowComponent } from '../components/article-row.component';
import { CollectionMenuComponent } from '../components/collection-menu.component';
import { NewsChipRowComponent } from '../components/news-chip-row.component';
import { NewsSkeletonComponent } from '../components/news-skeleton.component';
import { NewsStateComponent } from '../components/news-state.component';
import {
  NewsErrorCode,
  NewsOption,
  SavedArticle,
  SavedFilter,
  newsErrorCode,
  newsErrorMessage,
  savedToArticleView,
} from '../models/news.models';
import { NewsService } from '../services/news.service';
import { expiresSoon, expiryLabel, savedAgoLabel } from '../utils/news-dates';

const PAGE_SIZE = 20;

const EMPTY_TITLES: Record<SavedFilter, string> = {
  all: 'No saved articles yet',
  recent: 'Nothing saved in the last 7 days',
  expiring: 'Nothing expiring in the next 3 days',
};

@Component({
  selector: 'app-news-saved-tab',
  standalone: true,
  imports: [
    ArticleRowComponent,
    CollectionMenuComponent,
    ListPaginatorComponent,
    NewsChipRowComponent,
    NewsSkeletonComponent,
    NewsStateComponent,
  ],
  template: `
    <section class="space-y-3" aria-labelledby="news-saved-heading">
      <h2 id="news-saved-heading" class="section-heading">Saved Articles</h2>
      <app-news-chip-row label="Saved filter" [options]="filters" [selected]="filter()" (selectedChange)="setFilter($event)" />

      @if (loading()) {
        <app-news-skeleton layout="list" [count]="4" />
      } @else if (error()) {
        <app-news-state title="We couldn't load your saved articles." [message]="message(error()!)" [retryable]="true" (retry)="load()" />
      } @else if (items().length === 0) {
        <app-news-state [title]="emptyTitle()" message="Save articles with the star to read them later. Saved articles expire automatically." />
      } @else {
        <div class="space-y-2">
          @for (s of items(); track s.id) {
            <app-article-row [article]="view(s)">
              <p meta class="text-xs" style="color: var(--text-muted)">
                {{ savedAgo(s.saved_at) }} ·
                <span [style.color]="soon(s.expires_at) ? 'var(--warning)' : null">{{ expiry(s.expires_at) }}</span>
              </p>
              <app-collection-menu
                [savedArticleId]="s.id"
                [collectionIds]="s.collection_ids"
                (collectionIdsChange)="setCollections(s, $event)"
              />
              <button
                type="button"
                class="btn-ghost !min-h-8 !px-2 text-xs"
                aria-label="Remove saved article"
                data-testid="news-saved-remove-button"
                (click)="remove(s)"
              >
                Remove
              </button>
            </app-article-row>
          }
        </div>
        <app-list-paginator
          [total]="page.total"
          [pageSize]="page.pageSize"
          [currentPage]="page.currentPage"
          (pageChange)="goTo($event)"
        />
      }
      @if (actionError()) {
        <p class="text-xs" style="color: var(--danger)" role="alert">{{ actionError() }}</p>
      }
    </section>
  `,
})
export class NewsSavedTabComponent implements OnInit {
  private readonly news = inject(NewsService);
  private readonly confirm = inject(ConfirmService);

  readonly filters: readonly NewsOption<SavedFilter>[] = [
    { id: 'all', label: 'All' },
    { id: 'recent', label: 'Recent' },
    { id: 'expiring', label: 'Expiring Soon' },
  ];
  readonly page = new PaginatedListState(PAGE_SIZE);
  readonly filter = signal<SavedFilter>('all');
  readonly items = signal<SavedArticle[]>([]);
  readonly loading = signal(true);
  readonly error = signal<NewsErrorCode | null>(null);
  readonly actionError = signal<string | null>(null);

  readonly view = savedToArticleView;
  readonly savedAgo = (iso: string) => savedAgoLabel(iso);
  readonly expiry = (iso: string) => expiryLabel(iso);
  readonly soon = (iso: string) => expiresSoon(iso);
  readonly message = newsErrorMessage;

  ngOnInit(): void {
    this.load();
  }

  emptyTitle(): string {
    return EMPTY_TITLES[this.filter()];
  }

  setFilter(id: string): void {
    this.filter.set(id as SavedFilter);
    this.page.setPage(1);
    this.load();
  }

  goTo(pageNumber: number): void {
    this.page.setPage(pageNumber);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.news.listSaved(this.filter(), this.page.pageSize, this.page.offset).subscribe({
      next: (res) => {
        this.page.total = res.total;
        this.items.set(res.items);
        this.loading.set(false);
        // A removal can leave the current page empty; step back one page.
        if (res.items.length === 0 && this.page.currentPage > 1) this.goTo(this.page.currentPage - 1);
      },
      error: (err: unknown) => {
        this.error.set(newsErrorCode(err));
        this.loading.set(false);
      },
    });
  }

  setCollections(saved: SavedArticle, ids: string[]): void {
    this.items.update((list) => list.map((s) => (s.id === saved.id ? { ...s, collection_ids: ids } : s)));
  }

  async remove(saved: SavedArticle): Promise<void> {
    const ok = await this.confirm.confirm(`Remove "${saved.title}" from saved articles?`, 'Remove saved article');
    if (!ok) return;
    this.actionError.set(null);
    this.news.removeSaved(saved.id).subscribe({
      next: () => {
        this.news.invalidateNews();
        this.load();
      },
      error: (err: unknown) => this.actionError.set(newsErrorMessage(newsErrorCode(err))),
    });
  }
}
