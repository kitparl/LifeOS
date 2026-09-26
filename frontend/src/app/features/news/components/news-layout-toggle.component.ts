import { Component, inject } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import {
  NEWS_LAYOUT_OPTIONS,
  NewsLayout,
  NewsPreferencesService,
} from '../../../core/services/news-preferences.service';

const ICONS: Record<NewsLayout, string> = { list: 'list', grid: 'layout-grid', cards: 'layout-panel-top' };

/** Icon switcher for the live-feed layout; the choice is saved as a News preference. */
@Component({
  selector: 'app-news-layout-toggle',
  standalone: true,
  imports: [LucideDynamicIcon],
  template: `
    <div class="flex shrink-0 gap-1" role="group" aria-label="Layout">
      @for (o of options; track o.value) {
        <button
          type="button"
          class="btn-ghost !min-h-8 !px-2"
          [style.background]="o.value === prefs.layout() ? 'var(--primary-soft)' : null"
          [style.color]="o.value === prefs.layout() ? 'var(--primary-hover)' : null"
          [attr.aria-pressed]="o.value === prefs.layout()"
          [attr.title]="o.label"
          [attr.data-testid]="'news-layout-' + o.value"
          (click)="prefs.setLayout(o.value)"
        >
          <svg class="h-4 w-4" [lucideIcon]="icons[o.value]" aria-hidden="true"></svg>
          <span class="sr-only">{{ o.label }}</span>
        </button>
      }
    </div>
  `,
})
export class NewsLayoutToggleComponent {
  readonly prefs = inject(NewsPreferencesService);
  readonly options = NEWS_LAYOUT_OPTIONS;
  readonly icons = ICONS;
}
