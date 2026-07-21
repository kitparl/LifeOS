import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ListPaginatorComponent } from '../../shared/pagination/list-paginator.component';
import { QAListItem } from './models/qa.models';
import { QAService } from './services/qa.service';

@Component({
  selector: 'app-qa-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe, ListPaginatorComponent],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Personal Q&A</h1>
        <a routerLink="/qa/new" class="btn-primary text-xs no-underline">New Q&A</a>
      </div>

      <form class="flex flex-wrap gap-2 text-sm" [formGroup]="filters" (ngSubmit)="applyFilters()">
        <input class="input-field !w-48" formControlName="search" placeholder="Search…" />
        <select class="input-field !w-auto" formControlName="type">
          <option value="">All types</option>
          @for (t of types(); track t) {
            <option [value]="t">{{ t }}</option>
          }
        </select>
        <button type="submit" class="btn-primary text-xs">Filter</button>
      </form>

      @if (loading) {
        <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
      } @else if (entries.length === 0) {
        <div class="panel">
          <p class="text-sm" style="color: var(--text-muted)">No Q&A entries yet.</p>
          <a routerLink="/qa/new" class="btn-primary mt-2 inline-block text-xs no-underline">Create one</a>
        </div>
      } @else {
        <div class="space-y-3 md:hidden">
          @for (entry of pagedEntries; track entry.id) {
            <article class="panel space-y-2">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <a [routerLink]="['/qa', entry.id]" class="block truncate text-sm font-semibold text-[var(--xp-blue)] underline">
                    {{ entry.question }}
                  </a>
                  <p class="mt-1 flex flex-wrap items-center gap-2 truncate text-xs text-[var(--text-muted)]">
                    @if (entry.type) {
                      <span class="qa-type-badge">{{ entry.type }}</span>
                    }
                    <span>{{ entry.tags.join(', ') || 'No tags' }} · {{ entry.updated_at | date: 'mediumDate' }}</span>
                  </p>
                </div>
                <a [routerLink]="['/qa', entry.id, 'edit']" class="text-xs underline">Edit</a>
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
                <th class="px-3 py-2">Question</th>
                <th class="px-3 py-2">Type</th>
                <th class="px-3 py-2">Tags</th>
                <th class="px-3 py-2">Updated</th>
                <th class="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              @for (entry of pagedEntries; track entry.id) {
                <tr class="border-b border-[var(--xp-border)] hover:bg-[var(--primary-soft)]">
                  <td class="px-3 py-2 max-w-md">
                    <a [routerLink]="['/qa', entry.id]" class="link">{{ entry.question }}</a>
                  </td>
                  <td class="px-3 py-2 text-xs">
                    @if (entry.type) {
                      <span class="qa-type-badge">{{ entry.type }}</span>
                    } @else {
                      <span style="color: var(--text-faint)">—</span>
                    }
                  </td>
                  <td class="px-3 py-2 text-xs" style="color: var(--text-muted)">{{ entry.tags.join(', ') || '—' }}</td>
                  <td class="px-3 py-2 text-xs">{{ entry.updated_at | date: 'mediumDate' }}</td>
                  <td class="px-3 py-2">
                    <a [routerLink]="['/qa', entry.id, 'edit']" class="text-xs underline">Edit</a>
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
export class QAListComponent implements OnInit {
  private readonly qaService = inject(QAService);
  private readonly fb = inject(FormBuilder);

  entries: QAListItem[] = [];
  loading = false;
  currentPage = 1;
  readonly pageSize = 12;
  readonly types = signal<string[]>([]);
  filters = this.fb.nonNullable.group({ search: '', type: '' });

  ngOnInit(): void {
    this.qaService.listTypes().subscribe({ next: (t) => this.types.set(t) });
    this.load();
  }

  get pagedEntries(): QAListItem[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.entries.slice(start, start + this.pageSize);
  }

  applyFilters(): void {
    this.currentPage = 1;
    this.load();
  }

  load(): void {
    this.loading = true;
    const { search, type } = this.filters.getRawValue();
    this.qaService.list(search || undefined, type || undefined).subscribe({
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
