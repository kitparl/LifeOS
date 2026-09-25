import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { TabHubComponent } from '../../shared/tab-hub/tab-hub.component';
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

/** News module: live news from FreeNewsAPI plus the user's saved articles and collections. */
@Component({
  selector: 'app-news-hub',
  standalone: true,
  imports: [
    TabHubComponent,
    NewsLatestTabComponent,
    NewsCategoriesTabComponent,
    NewsSearchTabComponent,
    NewsSavedTabComponent,
    NewsCollectionsTabComponent,
  ],
  template: `
    <div class="space-y-3">
      <div class="overflow-x-auto">
        <app-tab-hub [tabs]="tabs" [activeId]="tab()" (tabChange)="setTab($event)" />
      </div>

      @switch (tab()) {
        @case ('categories') {
          <app-news-categories-tab />
        }
        @case ('search') {
          <app-news-search-tab />
        }
        @case ('saved') {
          <app-news-saved-tab />
        }
        @case ('collections') {
          <app-news-collections-tab />
        }
        @default {
          <app-news-latest-tab />
        }
      }
    </div>
  `,
})
export class NewsHubComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  readonly tabs = TABS;
  readonly tab = signal<NewsTab>('latest');

  ngOnInit(): void {
    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      const t = params.get('tab');
      this.tab.set(TABS.some((x) => x.id === t) ? (t as NewsTab) : 'latest');
    });
  }

  setTab(id: string): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tab: id === 'latest' ? null : id },
      queryParamsHandling: 'merge',
    });
  }
}
