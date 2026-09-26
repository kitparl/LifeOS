import { Component, computed, inject, signal } from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { LucideDynamicIcon } from '@lucide/angular';
import { debounceTime, distinctUntilChanged, map } from 'rxjs';
import { NewsPreferencesService } from '../../../core/services/news-preferences.service';
import { NewsFeedComponent } from '../components/news-feed.component';
import { NewsStateComponent } from '../components/news-state.component';
import {
  NEWS_COUNTRIES,
  NEWS_DATE_OPTIONS,
  NEWS_HOST_PATTERN,
  NEWS_LANGUAGES,
  NEWS_SORT_OPTIONS,
  NewsDatePreset,
  NewsQuery,
  NewsSort,
} from '../models/news.models';

/** Wait this long after typing stops before searching (no request per keystroke). */
export const SEARCH_DEBOUNCE_MS = 400;

@Component({
  selector: 'app-news-search-tab',
  standalone: true,
  imports: [LucideDynamicIcon, NewsFeedComponent, NewsStateComponent],
  template: `
    <section class="space-y-3" aria-labelledby="news-search-heading">
      <h2 id="news-search-heading" class="section-heading">Search News</h2>
      <div class="relative">
        <svg
          class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2"
          style="color: var(--text-faint)"
          lucideIcon="search"
          aria-hidden="true"
        ></svg>
        <label class="sr-only" for="news-search-input">Search news</label>
        <input
          id="news-search-input"
          type="search"
          class="input-field w-full"
          style="padding-left: 2.5rem"
          maxlength="200"
          placeholder="e.g. artificial intelligence"
          autocomplete="off"
          data-testid="news-search-input"
          [value]="text()"
          (input)="text.set($any($event.target).value)"
        />
      </div>

      <div class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5" role="group" aria-label="Filters">
        <label class="text-xs">
          <span class="form-label">Country</span>
          <select class="input-field w-full" data-testid="news-search-country-select" (change)="country.set($any($event.target).value)">
            @for (o of countries; track o.id) {
              <option [value]="o.id" [selected]="o.id === country()">{{ o.label }}</option>
            }
          </select>
        </label>
        <label class="text-xs">
          <span class="form-label">Language</span>
          <select class="input-field w-full" data-testid="news-search-language-select" (change)="lang.set($any($event.target).value)">
            @for (o of languages; track o.id) {
              <option [value]="o.id" [selected]="o.id === lang()">{{ o.label }}</option>
            }
          </select>
        </label>
        <label class="text-xs">
          <span class="form-label">Date</span>
          <select class="input-field w-full" data-testid="news-search-date-select" (change)="date.set($any($event.target).value)">
            @for (o of dates; track o.id) {
              <option [value]="o.id" [selected]="o.id === date()">{{ o.label }}</option>
            }
          </select>
        </label>
        <label class="text-xs">
          <span class="form-label">Publisher</span>
          <input
            class="input-field w-full"
            maxlength="253"
            placeholder="e.g. www.thehindu.com"
            data-testid="news-search-publisher-input"
            [attr.aria-invalid]="hostInvalid()"
            [value]="hostText()"
            (input)="hostText.set($any($event.target).value)"
          />
        </label>
        <label class="text-xs">
          <span class="form-label">Sort</span>
          <select class="input-field w-full" data-testid="news-search-sort-select" (change)="sort.set($any($event.target).value)">
            @for (o of sorts; track o.id) {
              <option [value]="o.id" [selected]="o.id === sort()">{{ o.label }}</option>
            }
          </select>
        </label>
      </div>
      @if (hostInvalid()) {
        <p class="text-xs" style="color: var(--danger)" role="alert">Enter a publisher domain like www.thehindu.com.</p>
      }

      @if (query()) {
        <app-news-feed [query]="query()" [layout]="prefs.layout()" emptyTitle="No results" />
      } @else {
        <app-news-state title="Search the latest news" message="Type a topic, person or place to begin." />
      }
    </section>
  `,
})
export class NewsSearchTabComponent {
  readonly prefs = inject(NewsPreferencesService);
  readonly countries = NEWS_COUNTRIES;
  readonly languages = NEWS_LANGUAGES;
  readonly dates = NEWS_DATE_OPTIONS;
  readonly sorts = NEWS_SORT_OPTIONS;

  readonly text = signal('');
  readonly hostText = signal('');
  readonly country = signal('');
  readonly lang = signal('en');
  readonly date = signal<NewsDatePreset | ''>('');
  readonly sort = signal<NewsSort>('date');

  private readonly debouncedText = toSignal(
    toObservable(this.text).pipe(debounceTime(SEARCH_DEBOUNCE_MS), map((v) => v.trim()), distinctUntilChanged()),
    { initialValue: '' },
  );
  private readonly debouncedHost = toSignal(
    toObservable(this.hostText).pipe(debounceTime(SEARCH_DEBOUNCE_MS), map((v) => v.trim().toLowerCase()), distinctUntilChanged()),
    { initialValue: '' },
  );

  readonly hostInvalid = computed(() => !!this.debouncedHost() && !NEWS_HOST_PATTERN.test(this.debouncedHost()));

  /** `null` until there is something to search for. Invalid publisher text is not sent. */
  readonly query = computed<NewsQuery | null>(() => {
    const q = this.debouncedText();
    if (!q) return null;
    return {
      q,
      country: this.country() || undefined,
      lang: this.lang() || undefined,
      date: this.date() || undefined,
      host: this.hostInvalid() ? undefined : this.debouncedHost() || undefined,
      sort: this.sort(),
    };
  });
}
