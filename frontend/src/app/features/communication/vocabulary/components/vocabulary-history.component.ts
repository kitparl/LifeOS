import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ListPaginatorComponent } from '../../../../shared/pagination/list-paginator.component';
import { HistoryEntry } from '../models/vocabulary.models';
import { VocabularyService } from '../services/vocabulary.service';

const PAGE_SIZE = 20;

/** Learning history grouped by date (PRD §51). Reflects what was actually shown —
 * the backend already resolves changed-word substitutions before this renders.
 * Click a date to expand/collapse the full vocabulary list for that day. */
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
        <div class="panel !p-0 overflow-hidden text-sm">
          <button
            type="button"
            class="flex w-full items-center justify-between gap-2 px-3 py-2 text-left hover:bg-[var(--surface-2)]"
            (click)="toggle(entry.set_id)"
          >
            <span class="flex items-center gap-2">
              <span class="text-xs" style="color: var(--text-muted)">{{ isExpanded(entry.set_id) ? '▾' : '▸' }}</span>
              <span class="font-semibold">{{ entry.set_date }}</span>
            </span>
            <span style="color: var(--text-muted)">
              {{ entry.item_count }} vocabulary · {{ entry.status === 'accepted' ? 'Accepted' : 'In Progress' }}
            </span>
          </button>

          @if (isExpanded(entry.set_id)) {
            <div class="grid gap-2 border-t p-3 sm:grid-cols-2" style="border-color: var(--border)">
              @for (item of entry.items; track item.id) {
                <button
                  type="button"
                  class="panel text-left text-sm"
                  (click)="openDetail(item.id)"
                >
                  <p class="font-semibold">{{ item.term }}</p>
                  <p class="text-xs" style="color: var(--text-muted)">{{ item.part_of_speech }} · {{ item.level }}</p>
                  <p>{{ item.simple_meaning }}</p>
                </button>
              }
            </div>
          } @else {
            <p class="px-3 pb-2 text-xs" style="color: var(--text-muted)">{{ termList(entry) }}</p>
          }
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
  private readonly router = inject(Router);

  readonly pageSize = PAGE_SIZE;
  readonly entries = signal<HistoryEntry[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly error = signal<string | null>(null);
  readonly expandedIds = signal<ReadonlySet<string>>(new Set());

  ngOnInit(): void {
    this.load();
  }

  termList(entry: HistoryEntry): string {
    return entry.items.map((i) => i.term).join(', ');
  }

  isExpanded(setId: string): boolean {
    return this.expandedIds().has(setId);
  }

  toggle(setId: string): void {
    const next = new Set(this.expandedIds());
    if (next.has(setId)) {
      next.delete(setId);
    } else {
      next.add(setId);
    }
    this.expandedIds.set(next);
  }

  openDetail(vocabularyId: string): void {
    this.router.navigate(['/communication/vocabulary', vocabularyId]);
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
