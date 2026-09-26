import { Component, computed, inject, linkedSignal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { catchError, of } from 'rxjs';
import { NewsPreferencesService } from '../../../core/services/news-preferences.service';
import { NewsChipRowComponent } from '../components/news-chip-row.component';
import { NewsFeedComponent } from '../components/news-feed.component';
import { NewsSkeletonComponent } from '../components/news-skeleton.component';
import { NewsStateComponent } from '../components/news-state.component';
import { NewsCategory, NewsQuery } from '../models/news.models';
import { NewsService } from '../services/news.service';
import { NEWS_CATEGORY_KEY, readNewsPref, writeNewsPref } from '../utils/news-prefs';

@Component({
  selector: 'app-news-categories-tab',
  standalone: true,
  imports: [NewsChipRowComponent, NewsFeedComponent, NewsSkeletonComponent, NewsStateComponent],
  template: `
    <section class="space-y-3" aria-labelledby="news-categories-heading">
      <h2 id="news-categories-heading" class="section-heading">Categories</h2>
      @if (categories(); as list) {
        @if (list.length) {
          <app-news-chip-row label="Category" [options]="list" [selected]="category()" (selectedChange)="setCategory($event)" />
          <app-news-feed [query]="query()" [layout]="prefs.layout()" emptyTitle="No news in this category right now" />
        } @else {
          <app-news-state title="Categories are unavailable." message="Please try again later." />
        }
      } @else {
        <app-news-skeleton />
      }
    </section>
  `,
})
export class NewsCategoriesTabComponent {
  private readonly news = inject(NewsService);
  readonly prefs = inject(NewsPreferencesService);

  readonly categories = toSignal<NewsCategory[] | null>(
    this.news.categories().pipe(catchError(() => of([] as NewsCategory[]))),
    { initialValue: null },
  );
  /** The default-view category when one is set, else the last one picked on this device. */
  private readonly chosen = linkedSignal(() => this.prefs.defaultCategory() ?? readNewsPref(NEWS_CATEGORY_KEY) ?? 'ai');
  /** The remembered category if it still exists, else the first one. */
  readonly category = computed(() => {
    const list = this.categories() ?? [];
    return list.some((c) => c.id === this.chosen()) ? this.chosen() : (list[0]?.id ?? '');
  });
  readonly query = computed<NewsQuery | null>(() =>
    this.category() ? { category: this.category(), lang: 'en', sort: 'date' } : null,
  );

  setCategory(id: string): void {
    this.chosen.set(id);
    writeNewsPref(NEWS_CATEGORY_KEY, id);
  }
}
