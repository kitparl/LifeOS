import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ListPaginatorComponent } from '../../../../shared/pagination/list-paginator.component';
import { VocabularyCard } from '../models/vocabulary.models';
import { VocabularyService } from '../services/vocabulary.service';

const PAGE_SIZE = 20;

/** Server-side search + filters over the master dataset (PRD §26-27, §50). */
@Component({
  selector: 'app-vocabulary-library',
  standalone: true,
  imports: [ListPaginatorComponent],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap gap-2">
        <input
          type="text"
          class="input-field"
          placeholder="Search term or meaning..."
          [value]="q()"
          (input)="onQueryInput($event)"
        />
        <select class="input-field" [value]="level()" (change)="onLevelChange($event)">
          <option value="">All levels</option>
          @for (l of levels; track l) {
            <option [value]="l">{{ l }}</option>
          }
        </select>
        <select class="input-field" [value]="type()" (change)="onTypeChange($event)">
          <option value="">All types</option>
          @for (t of types; track t) {
            <option [value]="t">{{ t }}</option>
          }
        </select>
      </div>

      @if (error()) {
        <p class="text-sm" style="color: var(--danger)">{{ error() }}</p>
      }

      <div class="grid gap-2 sm:grid-cols-2">
        @for (item of items(); track item.id) {
          <button type="button" class="panel text-left text-sm" (click)="openDetail(item.id)">
            <p class="font-semibold">{{ item.term }}</p>
            <p class="text-xs" style="color: var(--text-muted)">{{ item.part_of_speech }} · {{ item.level }}</p>
            <p>{{ item.simple_meaning }}</p>
          </button>
        }
      </div>

      @if (!items().length && !loading()) {
        <p class="text-sm" style="color: var(--text-muted)">No matching vocabulary found.</p>
      }

      <app-list-paginator [total]="total()" [pageSize]="pageSize" [currentPage]="page()" (pageChange)="setPage($event)" />
    </div>
  `,
})
export class VocabularyLibraryComponent implements OnInit {
  private readonly vocabularyService = inject(VocabularyService);
  private readonly router = inject(Router);

  readonly levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];
  readonly types = ['WORD', 'PHRASAL_VERB', 'COLLOCATION', 'COMMON_EXPRESSION', 'FUNCTIONAL_PHRASE'];
  readonly pageSize = PAGE_SIZE;

  readonly items = signal<VocabularyCard[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly q = signal('');
  readonly level = signal('');
  readonly type = signal('');
  readonly error = signal<string | null>(null);
  readonly loading = signal(false);

  private searchDebounce?: ReturnType<typeof setTimeout>;

  ngOnInit(): void {
    this.load();
  }

  onQueryInput(event: Event): void {
    this.q.set((event.target as HTMLInputElement).value);
    clearTimeout(this.searchDebounce);
    this.searchDebounce = setTimeout(() => {
      this.page.set(1);
      this.load();
    }, 300);
  }

  onLevelChange(event: Event): void {
    this.level.set((event.target as HTMLSelectElement).value);
    this.page.set(1);
    this.load();
  }

  onTypeChange(event: Event): void {
    this.type.set((event.target as HTMLSelectElement).value);
    this.page.set(1);
    this.load();
  }

  setPage(page: number): void {
    this.page.set(page);
    this.load();
  }

  openDetail(id: string): void {
    this.router.navigate(['/communication/vocabulary', id]);
  }

  load(): void {
    this.loading.set(true);
    const offset = (this.page() - 1) * this.pageSize;
    this.vocabularyService
      .search(
        {
          q: this.q() || undefined,
          level: (this.level() as never) || undefined,
          type: (this.type() as never) || undefined,
        },
        this.pageSize,
        offset,
      )
      .subscribe({
        next: (res) => {
          this.items.set(res.items);
          this.total.set(res.total);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('Could not load the vocabulary library.');
          this.loading.set(false);
        },
      });
  }
}
