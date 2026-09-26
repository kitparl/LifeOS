import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { catchError, of } from 'rxjs';
import {
  NEWS_DEFAULT_VIEW_LATEST,
  NEWS_LAYOUT_OPTIONS,
  NewsPreferencesService,
} from '../../core/services/news-preferences.service';
import { NewsCategory } from '../news/models/news.models';
import { NewsService } from '../news/services/news.service';

@Component({
  selector: 'app-settings-news-section',
  standalone: true,
  template: `
    <div class="panel max-w-md space-y-4">
      <div>
        <label class="form-label" for="news-default-view">Opens to</label>
        <select
          id="news-default-view"
          class="input-field"
          data-testid="settings-news-default-view"
          (change)="newsPrefs.setDefaultView($any($event.target).value)"
        >
          <option [value]="latest" [selected]="newsPrefs.defaultView() === latest">Latest</option>
          @for (c of categories(); track c.id) {
            <option [value]="c.id" [selected]="newsPrefs.defaultView() === c.id">{{ c.label }}</option>
          }
        </select>
      </div>

      <div class="space-y-2">
        <p class="form-label">Layout</p>
        <div class="flex flex-wrap gap-2">
          @for (option of layouts; track option.value) {
            <button
              type="button"
              class="text-xs"
              [class.btn-primary]="newsPrefs.layout() === option.value"
              [class.btn-secondary]="newsPrefs.layout() !== option.value"
              (click)="newsPrefs.setLayout(option.value)"
            >
              {{ option.label }}
            </button>
          }
        </div>
      </div>
    </div>
  `,
})
export class SettingsNewsSectionComponent {
  readonly newsPrefs = inject(NewsPreferencesService);
  readonly latest = NEWS_DEFAULT_VIEW_LATEST;

  /** Empty on failure: "Latest" stays selectable. */
  readonly categories = toSignal(
    inject(NewsService).categories().pipe(catchError(() => of([] as NewsCategory[]))),
    { initialValue: [] as NewsCategory[] },
  );

  readonly layouts = NEWS_LAYOUT_OPTIONS;
}
