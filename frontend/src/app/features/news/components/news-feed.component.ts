import { Component, DestroyRef, input, inject, signal } from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import { EMPTY, Observable, Subject, Subscription, catchError, distinctUntilChanged, merge, switchMap, tap } from 'rxjs';
import {
  NewsArticle,
  NewsArticlePage,
  NewsErrorCode,
  NewsQuery,
  newsErrorCode,
  newsErrorMessage,
  toArticleView,
} from '../models/news.models';
import { NewsService } from '../services/news.service';
import { ArticleCardComponent } from './article-card.component';
import { ArticleRowComponent } from './article-row.component';
import { NewsSkeletonComponent } from './news-skeleton.component';
import { NewsStateComponent } from './news-state.component';
import { NewsSaveButtonComponent } from './save-button.component';

const PAGE_SIZE = 20;

/**
 * Live news list for a query: cancels stale requests when the query changes, pages with
 * "Load more", and drops articles already shown (by id or URL) when appending.
 */
@Component({
  selector: 'app-news-feed',
  standalone: true,
  imports: [ArticleCardComponent, ArticleRowComponent, NewsSkeletonComponent, NewsStateComponent, NewsSaveButtonComponent],
  template: `
    @if (loading()) {
      <app-news-skeleton [layout]="layout()" />
    } @else if (error()) {
      <app-news-state title="We couldn't load the news." [message]="message(error()!)" [retryable]="true" (retry)="retry()" />
    } @else if (query() && items().length === 0) {
      <app-news-state [title]="emptyTitle()" message="Try a different filter or search." />
    } @else {
      @if (layout() === 'grid') {
        <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          @for (a of items(); track a.id) {
            <app-article-card [article]="view(a)">
              <app-news-save-button [article]="a" (savedChange)="onSaved(a, $event)" />
            </app-article-card>
          }
        </div>
      } @else {
        <div class="space-y-2">
          @for (a of items(); track a.id) {
            <app-article-row [article]="view(a)">
              <app-news-save-button [article]="a" (savedChange)="onSaved(a, $event)" />
            </app-article-row>
          }
        </div>
      }
      @if (hasMore()) {
        <div class="flex justify-center pt-3">
          <button
            type="button"
            class="btn-secondary"
            [disabled]="loadingMore()"
            data-testid="news-feed-load-more-button"
            (click)="loadMore()"
          >
            {{ loadingMore() ? 'Loading…' : 'Load more' }}
          </button>
        </div>
      }
      @if (moreError(); as code) {
        <p class="pt-2 text-center text-xs" style="color: var(--danger)" role="alert">{{ message(code) }}</p>
      }
    }
  `,
})
export class NewsFeedComponent {
  private readonly news = inject(NewsService);
  private readonly destroyRef = inject(DestroyRef);

  /** `null` means "nothing to show yet" (e.g. an empty search box): no request is made. */
  readonly query = input.required<NewsQuery | null>();
  readonly layout = input<'grid' | 'rows'>('grid');
  readonly emptyTitle = input('No news found');

  readonly items = signal<NewsArticle[]>([]);
  readonly loading = signal(false);
  readonly loadingMore = signal(false);
  readonly hasMore = signal(false);
  readonly error = signal<NewsErrorCode | null>(null);
  readonly moreError = signal<NewsErrorCode | null>(null);

  private readonly retry$ = new Subject<NewsQuery | null>();
  private nextOffset = 0;
  private moreSub: Subscription | undefined;

  readonly view = toArticleView;
  readonly message = newsErrorMessage;

  constructor() {
    const query$ = toObservable(this.query).pipe(distinctUntilChanged((a, b) => JSON.stringify(a) === JSON.stringify(b)));
    merge(query$, this.retry$)
      .pipe(
        tap(() => this.resetPaging()),
        switchMap((q) => (q ? this.firstPage(q) : EMPTY)),
        takeUntilDestroyed(),
      )
      .subscribe((page) => {
        this.items.set(page.items);
        this.applyPage(page);
        this.loading.set(false);
      });
  }

  retry(): void {
    this.retry$.next(this.query());
  }

  loadMore(): void {
    const q = this.query();
    if (!q || this.loadingMore()) return;
    this.loadingMore.set(true);
    this.moreError.set(null);
    this.moreSub = this.news
      .articles({ ...q, limit: PAGE_SIZE, offset: this.nextOffset })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
      next: (page) => {
        const seen = new Set(this.items().flatMap((a) => [a.id, a.url]));
        this.items.update((list) => [...list, ...page.items.filter((a) => !seen.has(a.id) && !seen.has(a.url))]);
        this.applyPage(page);
        this.loadingMore.set(false);
      },
      error: (err: unknown) => {
        this.moreError.set(newsErrorCode(err));
        this.loadingMore.set(false);
      },
    });
  }

  onSaved(article: NewsArticle, savedId: string | null): void {
    this.items.update((list) => list.map((a) => (a.id === article.id ? { ...a, saved_article_id: savedId } : a)));
  }

  private firstPage(q: NewsQuery): Observable<NewsArticlePage> {
    this.loading.set(true);
    return this.news.articles({ ...q, limit: PAGE_SIZE, offset: 0 }).pipe(
      catchError((err: unknown) => {
        this.error.set(newsErrorCode(err));
        this.loading.set(false);
        return EMPTY;
      }),
    );
  }

  private resetPaging(): void {
    this.moreSub?.unsubscribe();
    this.loadingMore.set(false);
    this.error.set(null);
    this.moreError.set(null);
    this.items.set([]);
    this.hasMore.set(false);
    this.nextOffset = 0;
  }

  private applyPage(page: NewsArticlePage): void {
    this.hasMore.set(page.has_more);
    this.nextOffset = page.offset + page.limit;
  }
}
