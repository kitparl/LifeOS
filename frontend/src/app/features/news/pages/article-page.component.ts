import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { catchError, map, of, startWith, switchMap } from 'rxjs';
import { NewsSaveButtonComponent } from '../components/save-button.component';
import { NewsSkeletonComponent } from '../components/news-skeleton.component';
import { NewsStateComponent } from '../components/news-state.component';
import { NewsThumbComponent } from '../components/news-thumb.component';
import { NewsArticleDetail, NewsErrorCode, newsErrorCode, newsErrorMessage, publisherOf } from '../models/news.models';
import { NewsService } from '../services/news.service';
import { fullDateTime } from '../utils/news-dates';

type ArticleState =
  | { kind: 'loading' }
  | { kind: 'loaded'; article: NewsArticleDetail }
  | { kind: 'error'; code: NewsErrorCode; url: string | null };

/** Article details: metadata, a short excerpt, and a link to the publisher (the full body is never shown). */
@Component({
  selector: 'app-news-article-page',
  standalone: true,
  imports: [RouterLink, LucideDynamicIcon, NewsSaveButtonComponent, NewsSkeletonComponent, NewsStateComponent, NewsThumbComponent],
  template: `
    <div class="mx-auto max-w-3xl space-y-3">
      <a class="btn-ghost !min-h-8 !px-2 text-xs" routerLink=".." data-testid="news-article-back-link">
        <svg class="h-3.5 w-3.5" lucideIcon="chevron-left" aria-hidden="true"></svg>
        News
      </a>

      @switch (state().kind) {
        @case ('loading') {
          <app-news-skeleton layout="rows" [count]="1" />
        }
        @case ('error') {
          @if (errorState(); as e) {
            <app-news-state
              [title]="e.code === 'article_unavailable' ? 'Article unavailable' : 'We couldn\\'t load this article.'"
              [message]="message(e.code)"
            />
            @if (e.url) {
              <div class="flex justify-center">
                <a class="btn-primary" [href]="e.url" target="_blank" rel="noopener noreferrer">Read Original Article →</a>
              </div>
            }
          }
        }
        @case ('loaded') {
          @if (article(); as a) {
            <article class="panel space-y-3">
              <header class="space-y-2">
                <h1 class="text-xl font-semibold leading-snug">{{ a.title }}</h1>
                <p class="text-xs" style="color: var(--text-muted)">
                  @if (publisher(a)) {
                    <span class="font-medium" style="color: var(--text)">{{ publisher(a) }}</span>
                  }
                  @if (a.author) {
                    <span> · {{ a.author }}</span>
                  }
                  @if (dateTime(a.published_at)) {
                    <span> · <time [attr.datetime]="a.published_at">{{ dateTime(a.published_at) }}</time></span>
                  }
                </p>
                <div class="flex flex-wrap items-center gap-2">
                  <a
                    class="btn-primary"
                    [href]="a.url"
                    target="_blank"
                    rel="noopener noreferrer"
                    data-testid="news-article-original-link"
                  >
                    Read Original Article →
                  </a>
                  <app-news-save-button [article]="a" />
                </div>
              </header>

              @if (a.image) {
                <app-news-thumb class="aspect-video w-full rounded" [src]="a.image" [alt]="a.title" />
              }
              @if (a.description) {
                <p class="text-sm font-medium">{{ a.description }}</p>
              }
              @if (a.excerpt.length) {
                <div class="space-y-2 text-sm leading-relaxed">
                  @for (p of a.excerpt; track $index) {
                    <p>{{ p }}</p>
                  }
                </div>
                <p class="text-xs" style="color: var(--text-muted)">
                  Excerpt. Read the full story on {{ publisher(a) || "the publisher's site" }}.
                </p>
              } @else if (!a.description) {
                <p class="text-sm" style="color: var(--text-muted)">No summary is available for this article.</p>
              }
            </article>
          }
        }
      }
    </div>
  `,
})
export class NewsArticlePageComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly news = inject(NewsService);

  readonly state = toSignal(
    this.route.queryParamMap.pipe(
      map((params) => params.get('url')),
      switchMap((url) => {
        if (!url) return of<ArticleState>({ kind: 'error', code: 'article_unavailable', url: null });
        return this.news.article(url).pipe(
          map((article): ArticleState => ({ kind: 'loaded', article })),
          catchError((err: unknown) => of<ArticleState>({ kind: 'error', code: newsErrorCode(err), url: safeUrl(url) })),
          startWith<ArticleState>({ kind: 'loading' }),
        );
      }),
    ),
    { initialValue: { kind: 'loading' } as ArticleState },
  );

  readonly publisher = publisherOf;
  readonly dateTime = fullDateTime;
  readonly message = newsErrorMessage;

  article(): NewsArticleDetail | null {
    const s = this.state();
    return s.kind === 'loaded' ? s.article : null;
  }

  errorState(): { code: NewsErrorCode; url: string | null } | null {
    const s = this.state();
    return s.kind === 'error' ? s : null;
  }
}

/** Only link out to http(s) URLs taken from the query string. */
function safeUrl(url: string): string | null {
  return /^https?:\/\//i.test(url) ? url : null;
}
