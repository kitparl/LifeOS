import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { NewsPreferencesService } from '../../core/services/news-preferences.service';
import { GuestLockedPanelComponent } from '../../shared/guest-locked/guest-locked-panel.component';
import { TabHubComponent } from '../../shared/tab-hub/tab-hub.component';
import { NewsLayoutToggleComponent } from './components/news-layout-toggle.component';
import { NEWS_ACCESS_MODE } from './news-access-mode';
import { NewsCategoriesTabComponent } from './pages/categories-tab.component';
import { NewsCollectionsTabComponent } from './pages/collections-tab.component';
import { NewsLatestTabComponent } from './pages/latest-tab.component';
import { NewsSavedTabComponent } from './pages/saved-tab.component';
import { NewsSearchTabComponent } from './pages/search-tab.component';

type NewsTab = 'latest' | 'categories' | 'search' | 'saved' | 'collections';

const TABS: { id: NewsTab; label: string }[] = [
  { id: 'latest', label: 'Latest' },
  { id: 'categories', label: 'Categories' },
  { id: 'search', label: 'Search' },
  { id: 'saved', label: 'Saved' },
  { id: 'collections', label: 'Collections' },
];

/** Tabs that render a live feed, where the layout switcher applies. */
const FEED_TABS: readonly NewsTab[] = ['latest', 'categories', 'search'];

/**
 * News module: live news from FreeNewsAPI plus the user's saved articles and collections.
 * Guests keep every tab, but Saved and Collections show a Sign in panel and load nothing.
 * Without a `?tab`, the hub opens on the user's default view (Latest or a category).
 */
@Component({
  selector: 'app-news-hub',
  standalone: true,
  imports: [
    GuestLockedPanelComponent,
    TabHubComponent,
    NewsLayoutToggleComponent,
    NewsLatestTabComponent,
    NewsCategoriesTabComponent,
    NewsSearchTabComponent,
    NewsSavedTabComponent,
    NewsCollectionsTabComponent,
  ],
  template: `
    <div class="space-y-3">
      <div class="flex items-center gap-2">
        <div class="min-w-0 flex-1 overflow-x-auto">
          <app-tab-hub [tabs]="tabs" [activeId]="tab()" (tabChange)="setTab($event)" />
        </div>
        @if (showLayoutToggle()) {
          <app-news-layout-toggle />
        }
      </div>

      @switch (tab()) {
        @case ('categories') {
          <app-news-categories-tab />
        }
        @case ('search') {
          <app-news-search-tab />
        }
        @case ('saved') {
          @if (isGuest) {
            <app-guest-locked-panel [message]="lockedMessage" testId="news-saved-locked" />
          } @else {
            <app-news-saved-tab />
          }
        }
        @case ('collections') {
          @if (isGuest) {
            <app-guest-locked-panel [message]="lockedMessage" testId="news-collections-locked" />
          } @else {
            <app-news-collections-tab />
          }
        }
        @default {
          <app-news-latest-tab />
        }
      }
    </div>
  `,
})
export class NewsHubComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly prefs = inject(NewsPreferencesService);

  readonly tabs = TABS;
  readonly isGuest = inject(NEWS_ACCESS_MODE) === 'guest';
  readonly lockedMessage = 'Saving and collections are part of your LifeOS account.';

  private readonly tabParam = toSignal(this.route.queryParamMap, { requireSync: true });
  readonly tab = computed<NewsTab>(() => {
    const t = this.tabParam().get('tab');
    if (TABS.some((x) => x.id === t)) return t as NewsTab;
    return this.prefs.defaultCategory() ? 'categories' : 'latest';
  });
  readonly showLayoutToggle = computed(() => FEED_TABS.includes(this.tab()));

  setTab(id: string): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab: id },
      queryParamsHandling: 'merge',
    });
  }
}
