import { Component, computed, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { ArticleView } from '../models/news.models';
import { formatAttribution } from './article-card.component';
import { NewsThumbComponent } from './news-thumb.component';

/** List row for search results and saved articles. Extra meta lines and actions are projected. */
@Component({
  selector: 'app-article-row',
  standalone: true,
  imports: [RouterLink, LucideDynamicIcon, NewsThumbComponent],
  template: `
    <article class="panel--flat relative flex gap-3 !p-3 has-[[aria-expanded=true]]:z-50">
      <a
        class="shrink-0"
        [routerLink]="['/news/article']"
        [queryParams]="{ url: article().url }"
        tabindex="-1"
        aria-hidden="true"
      >
        <app-news-thumb class="h-16 w-24 rounded sm:h-20 sm:w-32" [src]="article().image" />
      </a>
      <div class="flex min-w-0 flex-1 flex-col gap-1">
        <h3 class="text-sm font-semibold leading-snug">
          <a class="link" [routerLink]="['/news/article']" [queryParams]="{ url: article().url }" data-testid="article-row-title-link">
            {{ article().title }}
          </a>
        </h3>
        @if (attribution()) {
          <p class="text-xs" style="color: var(--text-muted)">{{ attribution() }}</p>
        }
        @if (article().description) {
          <p class="line-clamp-2 text-xs" style="color: var(--text-muted)">{{ article().description }}</p>
        }
        <ng-content select="[meta]" />
        <div class="flex flex-wrap items-center justify-end gap-1 pt-1">
          <a
            class="btn-ghost !min-h-8 !px-2 text-xs"
            [href]="article().url"
            target="_blank"
            rel="noopener noreferrer"
            data-testid="article-row-original-link"
          >
            <svg class="h-3.5 w-3.5" lucideIcon="external-link" aria-hidden="true"></svg>
            Original
            <span class="sr-only">(opens {{ article().publisher || 'publisher site' }} in a new tab)</span>
          </a>
          <ng-content />
        </div>
      </div>
    </article>
  `,
})
export class ArticleRowComponent {
  readonly article = input.required<ArticleView>();
  readonly attribution = computed(() => formatAttribution(this.article()));
}
