import { Component, computed, inject, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ArticleView } from '../models/news.models';
import { NEWS_ACCESS_MODE, newsRootPath } from '../news-access-mode';
import { relativeTime } from '../utils/news-dates';
import { NewsThumbComponent } from './news-thumb.component';

/** Grid card for a live article. Actions (save, collection) are projected. */
@Component({
  selector: 'app-article-card',
  standalone: true,
  imports: [RouterLink, NewsThumbComponent],
  template: `
    <article class="panel--flat relative flex h-full flex-col !p-0 has-[[aria-expanded=true]]:z-50">
      <a
        class="block overflow-hidden"
        style="border-radius: var(--radius-lg) var(--radius-lg) 0 0"
        [routerLink]="articleLink"
        [queryParams]="{ url: article().url }"
        tabindex="-1"
        aria-hidden="true"
      >
        <app-news-thumb class="aspect-video w-full" [src]="article().image" />
      </a>
      <div class="flex flex-1 flex-col gap-1.5 p-3">
        @if (article().category || article().country) {
          <div class="flex flex-wrap gap-1">
            @if (article().category) {
              <span class="badge badge--default">{{ article().category }}</span>
            }
            @if (article().country) {
              <span class="badge badge--default">{{ article().country }}</span>
            }
          </div>
        }
        <h3 class="text-sm font-semibold leading-snug">
          <a
            class="link"
            [routerLink]="articleLink"
            [queryParams]="{ url: article().url }"
            data-testid="article-card-title-link"
          >
            {{ article().title }}
          </a>
        </h3>
        @if (article().description) {
          <p class="line-clamp-3 text-xs" style="color: var(--text-muted)">{{ article().description }}</p>
        }
        <div class="mt-auto flex items-center justify-between gap-2 pt-1">
          <p class="min-w-0 truncate text-xs" style="color: var(--text-muted)">{{ attribution() }}</p>
          <div class="flex shrink-0 items-center gap-1">
            <ng-content />
          </div>
        </div>
      </div>
    </article>
  `,
})
export class ArticleCardComponent {
  readonly article = input.required<ArticleView>();
  /** Absolute: cards render on the hub and on collection pages (different route depths). */
  readonly articleLink = `${newsRootPath(inject(NEWS_ACCESS_MODE))}/article`;
  readonly attribution = computed(() => formatAttribution(this.article()));
}

/** "The Hindu · 2 hours ago" (parts omitted when unknown; never fabricated). */
export function formatAttribution(article: ArticleView): string {
  return [article.publisher, relativeTime(article.published_at)].filter(Boolean).join(' · ');
}
