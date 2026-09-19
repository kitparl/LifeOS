import { Component, OnInit, inject, signal } from '@angular/core';
import { ListPaginatorComponent } from '../../../../shared/pagination/list-paginator.component';
import { HistoryEntry } from '../models/vocabulary.models';
import { VocabularyService } from '../services/vocabulary.service';

const PAGE_SIZE = 20;

/** Learning history grouped by date (PRD §51). Reflects what was actually shown —
 * the backend already resolves changed-word substitutions before this renders. */
@Component({
  selector: 'app-vocabulary-history',
  standalone: true,
  imports: [ListPaginatorComponent],
  template: `
    <div class="space-y-3">
      @if (error()) {
        <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
      }

      @for (entry of entries(); track entry.set_id) {
        <div class="panel text-sm">
          <div class="flex items-center justify-between">
            <p class="font-semibold">{{ entry.set_date }}</p>
            <span style="color: var(--text-muted)">
              {{ entry.item_count }} vocabulary · {{ entry.status === 'accepted' ? 'Accepted' : 'In Progress' }}
            </span>
          </div>
          <p style="color: var(--text-muted)">{{ termList(entry) }}</p>
        </div>
      }

      @if (!entries().length) {
        <p class="text-sm" style="color: var(--text-muted)">No learning history yet.</p>
      }

      <app-list-paginator [total]="total()" [pageSize]="pageSize" [currentPage]="page()" (pageChange)="setPage($event)" />
    </div>
  `,
})
export class VocabularyHistoryComponent implements OnInit {
  private readonly vocabularyService = inject(VocabularyService);

  readonly pageSize = PAGE_SIZE;
  readonly entries = signal<HistoryEntry[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.load();
  }

  termList(entry: HistoryEntry): string {
    return entry.items.map((i) => i.term).join(', ');
  }

  setPage(page: number): void {
    this.page.set(page);
    this.load();
  }

  load(): void {
    const offset = (this.page() - 1) * this.pageSize;
    this.vocabularyService.getHistory(this.pageSize, offset).subscribe({
      next: (res) => {
        this.entries.set(res.items);
        this.total.set(res.total);
      },
      error: () => this.error.set('Could not load history.'),
    });
  }
}
