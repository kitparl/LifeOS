import { HttpStatusCode } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { ListPaginatorComponent } from '../../../shared/pagination/list-paginator.component';
import { PaginatedListState } from '../../../shared/pagination/paginated-list.state';
import { ArticleRowComponent } from '../components/article-row.component';
import { CollectionMenuComponent } from '../components/collection-menu.component';
import { NewsSkeletonComponent } from '../components/news-skeleton.component';
import { NewsStateComponent } from '../components/news-state.component';
import {
  NewsErrorCode,
  SavedArticle,
  newsErrorCode,
  newsErrorMessage,
  savedToArticleView,
} from '../models/news.models';
import { NewsService } from '../services/news.service';
import { expiresSoon, expiryLabel, savedAgoLabel } from '../utils/news-dates';

const PAGE_SIZE = 20;

@Component({
  selector: 'app-news-collection-page',
  standalone: true,
  imports: [
    RouterLink,
    LucideDynamicIcon,
    ArticleRowComponent,
    CollectionMenuComponent,
    ListPaginatorComponent,
    NewsSkeletonComponent,
    NewsStateComponent,
  ],
  template: `
    <div class="mx-auto max-w-3xl space-y-3">
      <a class="btn-ghost !min-h-8 !px-2 text-xs" routerLink="../.." [queryParams]="{ tab: 'collections' }">
        <svg class="h-3.5 w-3.5" lucideIcon="chevron-left" aria-hidden="true"></svg>
        Collections
      </a>

      @if (notFound()) {
        <app-news-state title="Collection not found" message="It may have been deleted." />
      } @else {
        <header>
          <h1 class="text-xl font-semibold">{{ name() }}</h1>
          <p class="text-xs" style="color: var(--text-muted)">
            {{ page.total }} saved {{ page.total === 1 ? 'article' : 'articles' }}
          </p>
        </header>

        @if (loading()) {
          <app-news-skeleton layout="list" [count]="4" />
        } @else if (error()) {
          <app-news-state title="We couldn't load this collection." [message]="message(error()!)" [retryable]="true" (retry)="load()" />
        } @else if (items().length === 0) {
          <app-news-state title="This collection is empty" message="Add saved articles from the Saved tab or any article's star menu." />
        } @else {
          <div class="space-y-2">
            @for (s of items(); track s.id) {
              <app-article-row [article]="view(s)">
                <p meta class="text-xs" style="color: var(--text-muted)">
                  {{ savedAgo(s.saved_at) }} ·
                  <span [style.color]="soon(s.expires_at) ? 'var(--warning)' : null">{{ expiry(s.expires_at) }}</span>
                </p>
                <app-collection-menu mode="move" [savedArticleId]="s.id" [sourceCollectionId]="collectionId" (moved)="load()" />
                <button
                  type="button"
                  class="btn-ghost !min-h-8 !px-2 text-xs"
                  data-testid="news-collection-remove-button"
                  (click)="removeFromCollection(s)"
                >
                  Remove from collection
                </button>
              </app-article-row>
            }
          </div>
          <app-list-paginator [total]="page.total" [pageSize]="page.pageSize" [currentPage]="page.currentPage" (pageChange)="goTo($event)" />
        }
        @if (actionError()) {
          <p class="text-xs" style="color: var(--danger)" role="alert">{{ actionError() }}</p>
        }
      }
    </div>
  `,
})
export class NewsCollectionPageComponent implements OnInit {
  private readonly news = inject(NewsService);
  readonly collectionId = inject(ActivatedRoute).snapshot.paramMap.get('id') ?? '';

  readonly page = new PaginatedListState(PAGE_SIZE);
  readonly name = signal('');
  readonly items = signal<SavedArticle[]>([]);
  readonly loading = signal(true);
  readonly notFound = signal(false);
  readonly error = signal<NewsErrorCode | null>(null);
  readonly actionError = signal<string | null>(null);

  readonly view = savedToArticleView;
  readonly savedAgo = (iso: string) => savedAgoLabel(iso);
  readonly expiry = (iso: string) => expiryLabel(iso);
  readonly soon = (iso: string) => expiresSoon(iso);
  readonly message = newsErrorMessage;

  ngOnInit(): void {
    // No single-collection endpoint: the name comes from the (small) collections list.
    this.news.listCollections().subscribe({
      next: (list) => this.name.set(list.find((c) => c.id === this.collectionId)?.name ?? ''),
      error: () => undefined,
    });
    this.load();
  }

  goTo(pageNumber: number): void {
    this.page.setPage(pageNumber);
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.news.listCollectionArticles(this.collectionId, this.page.pageSize, this.page.offset).subscribe({
      next: (res) => {
        this.page.total = res.total;
        this.items.set(res.items);
        this.loading.set(false);
        if (res.items.length === 0 && this.page.currentPage > 1) this.goTo(this.page.currentPage - 1);
      },
      error: (err: unknown) => {
        this.loading.set(false);
        if ((err as { status?: number })?.status === HttpStatusCode.NotFound) this.notFound.set(true);
        else this.error.set(newsErrorCode(err));
      },
    });
  }

  removeFromCollection(saved: SavedArticle): void {
    this.actionError.set(null);
    this.news.removeFromCollection(this.collectionId, saved.id).subscribe({
      next: () => this.load(),
      error: (err: unknown) => this.actionError.set(newsErrorMessage(newsErrorCode(err))),
    });
  }
}
