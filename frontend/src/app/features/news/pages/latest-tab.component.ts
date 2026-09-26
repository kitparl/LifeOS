import { Component, computed, inject, signal } from '@angular/core';
import { NewsPreferencesService } from '../../../core/services/news-preferences.service';
import { NewsChipRowComponent } from '../components/news-chip-row.component';
import { NewsFeedComponent } from '../components/news-feed.component';
import { NEWS_COUNTRIES, NewsQuery } from '../models/news.models';
import { NEWS_COUNTRY_KEY, readNewsPref, writeNewsPref } from '../utils/news-prefs';

@Component({
  selector: 'app-news-latest-tab',
  standalone: true,
  imports: [NewsChipRowComponent, NewsFeedComponent],
  template: `
    <section class="space-y-3" aria-labelledby="news-latest-heading">
      <h2 id="news-latest-heading" class="section-heading">Latest News</h2>
      <app-news-chip-row label="Country" [options]="countries" [selected]="country()" (selectedChange)="setCountry($event)" />
      <app-news-feed [query]="query()" [layout]="prefs.layout()" />
    </section>
  `,
})
export class NewsLatestTabComponent {
  readonly prefs = inject(NewsPreferencesService);
  readonly countries = NEWS_COUNTRIES;
  readonly country = signal(validCountry(readNewsPref(NEWS_COUNTRY_KEY)));
  readonly query = computed<NewsQuery>(() => ({ lang: 'en', sort: 'date', country: this.country() || undefined }));

  setCountry(id: string): void {
    this.country.set(id);
    writeNewsPref(NEWS_COUNTRY_KEY, id);
  }
}

function validCountry(value: string | null): string {
  return NEWS_COUNTRIES.some((c) => c.id === value) ? (value as string) : '';
}
