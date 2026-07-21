import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ListPaginatorComponent } from '../../shared/pagination/list-paginator.component';
import { MarkdownService } from '../../shared/markdown/markdown.service';
import { JOURNAL_TYPES, JournalListItem } from './models/journal.models';
import { JournalService } from './services/journal.service';

@Component({
  selector: 'app-journal-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe, ListPaginatorComponent],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Journal</h1>
        <a routerLink="/journal/new" class="btn-primary text-xs no-underline">New Entry</a>
      </div>

      <form class="flex flex-wrap gap-2 text-sm" [formGroup]="filters" (ngSubmit)="applyFilters()">
        <select class="input-field !w-auto" formControlName="entry_type">
          <option value="">All types</option>
          @for (t of types; track t.value) {
            <option [value]="t.value">{{ t.label }}</option>
          }
        </select>
        <input class="input-field !w-40" formControlName="search" placeholder="Search…" />
        <button type="submit" class="btn-primary text-xs">Filter</button>
      </form>

      @if (loading) {
        <p class="text-sm" style="color: var(--text-muted)">Loading entries…</p>
      } @else if (entries.length === 0) {
        <div class="panel">
          <p class="text-sm" style="color: var(--text-muted)">No journal entries yet.</p>
          <a routerLink="/journal/new" class="btn-primary mt-2 inline-block text-xs no-underline">Write entry</a>
        </div>
      } @else {
        <div class="space-y-3 md:hidden">
          @for (entry of pagedEntries; track entry.id) {
            <article class="panel space-y-2">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <a [routerLink]="['/journal', entry.id]" class="block truncate text-sm font-semibold text-[var(--xp-blue)] underline">
                    {{ entry.title || preview(entry.content) || 'Untitled entry' }}
                  </a>
                  <p class="mt-1 text-xs capitalize text-[var(--text-muted)]">
                    {{ entry.entry_type }} · {{ entry.entry_date | date: 'mediumDate' }}
                  </p>
                </div>
                <a [routerLink]="['/journal', entry.id, 'edit']" class="text-xs underline">Edit</a>
              </div>
            </article>
          }
          <app-list-paginator
            [total]="entries.length"
            [pageSize]="pageSize"
            [currentPage]="currentPage"
            (pageChange)="setPage($event)"
          />
        </div>
        <div class="panel hidden !p-0 overflow-hidden md:block">
          <table class="w-full text-sm">
            <thead class="border-b border-[var(--xp-border)] bg-[var(--xp-silver)] text-left">
              <tr>
                <th class="px-3 py-2">Date</th>
                <th class="px-3 py-2">Type</th>
                <th class="px-3 py-2">Preview</th>
                <th class="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              @for (entry of pagedEntries; track entry.id) {
                <tr class="border-b border-[var(--xp-border)] hover:bg-[var(--primary-soft)]">
                  <td class="px-3 py-2">{{ entry.entry_date | date: 'mediumDate' }}</td>
                  <td class="px-3 py-2 capitalize">{{ entry.entry_type }}</td>
                  <td class="px-3 py-2 max-w-xs truncate">
                    <a [routerLink]="['/journal', entry.id]" class="link">
                      {{ entry.title || preview(entry.content) || '—' }}
                    </a>
                  </td>
                  <td class="px-3 py-2">
                    <a [routerLink]="['/journal', entry.id, 'edit']" class="text-xs underline">Edit</a>
                  </td>
                </tr>
              }
            </tbody>
          </table>
          <app-list-paginator
            [total]="entries.length"
            [pageSize]="pageSize"
            [currentPage]="currentPage"
            (pageChange)="setPage($event)"
          />
        </div>
      }
    </div>
  `,
})
export class JournalListComponent implements OnInit {
  private readonly journalService = inject(JournalService);
  private readonly fb = inject(FormBuilder);
  private readonly markdown = inject(MarkdownService);

  types = JOURNAL_TYPES;

  preview(content: string): string {
    return this.markdown.toPlainText(content, 80);
  }
  entries: JournalListItem[] = [];
  loading = false;
  currentPage = 1;
  readonly pageSize = 12;

  filters = this.fb.nonNullable.group({ entry_type: '', search: '' });

  ngOnInit(): void {
    this.load();
  }

  get pagedEntries(): JournalListItem[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.entries.slice(start, start + this.pageSize);
  }

  applyFilters(): void {
    this.currentPage = 1;
    this.load();
  }

  load(): void {
    this.loading = true;
    const raw = this.filters.getRawValue();
    this.journalService
      .list(raw.entry_type || undefined, raw.search || undefined)
      .subscribe({
        next: (data) => {
          this.entries = data;
          this.clampPage();
          this.loading = false;
        },
        error: () => (this.loading = false),
      });
  }

  setPage(page: number): void {
    this.currentPage = page;
  }

  private clampPage(): void {
    const totalPages = Math.max(1, Math.ceil(this.entries.length / this.pageSize));
    this.currentPage = Math.min(this.currentPage, totalPages);
  }
}
