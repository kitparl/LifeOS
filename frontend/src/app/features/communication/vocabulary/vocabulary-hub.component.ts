import { Component, signal } from '@angular/core';
import { TabHubComponent, TabHubItem } from '../../../shared/tab-hub/tab-hub.component';
import { VocabularyBookmarksComponent } from './components/vocabulary-bookmarks.component';
import { VocabularyGamesComponent } from './components/vocabulary-games.component';
import { VocabularyHistoryComponent } from './components/vocabulary-history.component';
import { VocabularyLibraryComponent } from './components/vocabulary-library.component';
import { VocabularyProgressComponent } from './components/vocabulary-progress.component';
import { VocabularyWordLabComponent } from './components/vocabulary-word-lab.component';
import { VocabularyDailyComponent } from './vocabulary-daily.component';

type VocabTab = 'today' | 'bookmarks' | 'library' | 'history' | 'progress' | 'games' | 'word-lab';

@Component({
  selector: 'app-vocabulary-hub',
  standalone: true,
  imports: [
    TabHubComponent,
    VocabularyDailyComponent,
    VocabularyBookmarksComponent,
    VocabularyLibraryComponent,
    VocabularyHistoryComponent,
    VocabularyProgressComponent,
    VocabularyGamesComponent,
    VocabularyWordLabComponent,
  ],
  template: `
    <div class="space-y-3">
      <app-tab-hub [tabs]="tabs" [activeId]="activeTab()" [wrap]="true" (tabChange)="setTab($event)" />

      @switch (activeTab()) {
        @case ('today') {
          <app-vocabulary-daily />
        }
        @case ('bookmarks') {
          <app-vocabulary-bookmarks />
        }
        @case ('library') {
          <app-vocabulary-library />
        }
        @case ('history') {
          <app-vocabulary-history />
        }
        @case ('progress') {
          <app-vocabulary-progress (openBookmarks)="setTab('bookmarks')" />
        }
        @case ('games') {
          <app-vocabulary-games />
        }
        @case ('word-lab') {
          <app-vocabulary-word-lab />
        }
      }
    </div>
  `,
})
export class VocabularyHubComponent {
  readonly tabs: TabHubItem[] = [
    { id: 'today', label: "Today's Words" },
    { id: 'bookmarks', label: 'Bookmarks' },
    { id: 'library', label: 'Library' },
    { id: 'history', label: 'History' },
    { id: 'progress', label: 'Progress' },
    { id: 'games', label: 'Games' },
    { id: 'word-lab', label: 'Word Lab' },
  ];

  readonly activeTab = signal<VocabTab>('today');

  setTab(id: string): void {
    this.activeTab.set(id as VocabTab);
  }
}
