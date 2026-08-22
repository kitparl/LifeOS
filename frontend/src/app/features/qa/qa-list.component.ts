import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ListPaginatorComponent } from '../../shared/pagination/list-paginator.component';
import {
  QAExpandableEntryComponent,
  groupEntriesByMonth,
} from './qa-expandable-entry.component';
import { QAListItem, QAViewMode } from './models/qa.models';
import { QAService } from './services/qa.service';

interface ViewTab {
  id: QAViewMode;
  label: string;
}

@Component({
  selector: 'app-qa-list',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    DatePipe,
    ListPaginatorComponent,
    QAExpandableEntryComponent,
  ],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Personal Q&A</h1>
        <a routerLink="/qa/new" class="btn-primary text-xs no-underline">New Q&A</a>
      </div>

      <div class="flex flex-wrap gap-1.5 text-xs">
        @for (tab of viewTabs; track tab.id) {
          <button
            type="button"
            class="rounded-lg border px-3 py-1.5"
            [class.bg-[var(--primary-soft)]]="view === tab.id"
            [style.border-color]="'var(--xp-border)'"
            (click)="setView(tab.id)"
          >
            {{ tab.label }}
          </button>
        }
      </div>

      <form class="flex flex-wrap gap-2 text-sm" [formGroup]="filters" (ngSubmit)="applyFilters()">
        <input class="input-field !w-48" formControlName="search" placeholder="Search…" />
        <select class="input-field !w-auto" formControlName="type">
          <option value="">All types</option>
          @for (t of types(); track t) {
            <option [value]="t">{{ t }}</option>
          }
        </select>
        <input class="input-field !w-36" formControlName="tag" placeholder="Tag…" />
        <button type="submit" class="btn-primary text-xs">Filter</button>
      </form>

      @if (loading) {
        <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
      } @else if (entries.length === 0) {
        <div class="panel">
          <p class="text-sm" style="color: var(--text-muted)">{{ emptyMessage }}</p>
          @if (view === 'all') {
            <a routerLink="/qa/new" class="btn-primary mt-2 inline-block text-xs no-underline">New Q&A</a>
          }
        </div>
      } @else if (view === 'all') {
        <div class="space-y-3 md:hidden">
          @for (entry of entries; track entry.id) {
            <app-qa-expandable-entry
              [entry]="entry"
              [expanded]="isExpanded(entry.id)"
              [answer]="getAnswer(entry)"
              [loadingAnswer]="isLoadingAnswer(entry.id)"
              dateField="updated_at"
              (toggle)="toggleExpand($event)"
            />
          }
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
              @for (entry of entries; track entry.id) {
                <tr
                  class="border-b border-[var(--xp-border)] hover:bg-[var(--primary-soft)] cursor-pointer"
                  (click)="toggleExpand(entry.id)"
                >
                  <td class="px-3 py-2 max-w-md font-medium">{{ entry.question }}</td>
                  <td class="px-3 py-2 text-xs">
                    @if (entry.type) {
                      <span class="qa-type-badge">{{ entry.type }}</span>
                    } @else {
                      <span style="color: var(--text-faint)">—</span>
                    }
                  </td>
                  <td class="px-3 py-2 text-xs" style="color: var(--text-muted)">
                    {{ entry.tags.join(', ') || '—' }}
                  </td>
                  <td class="px-3 py-2 text-xs">{{ entry.updated_at | date: 'mediumDate' }}</td>
                  <td class="px-3 py-2 text-xs">{{ isExpanded(entry.id) ? '▲' : '▼' }}</td>
                </tr>
                @if (isExpanded(entry.id)) {
                  <tr class="border-b border-[var(--xp-border)] bg-[var(--primary-soft)]">
                    <td colspan="5" class="px-3 py-3 text-sm">
                      @if (isLoadingAnswer(entry.id)) {
                        <p class="text-xs" style="color: var(--text-muted)">Loading answer…</p>
                      } @else {
                        <p class="whitespace-pre-wrap">{{ getAnswer(entry) }}</p>
                      }
                      <a
                        [routerLink]="['/qa', entry.id, 'edit']"
                        class="mt-2 inline-block text-xs underline"
                        (click)="$event.stopPropagation()"
                      >Edit</a>
                    </td>
                  </tr>
                }
              }
            </tbody>
          </table>
        </div>
        <app-list-paginator
          [total]="total"
          [pageSize]="pageSize"
          [currentPage]="currentPage"
          (pageChange)="setPage($event)"
        />
      } @else {
        <div class="space-y-4">
          @for (group of monthGroups; track group.key) {
            <section>
              <h2 class="border-b border-[var(--xp-border)] pb-1 text-sm font-semibold">{{ group.label }}</h2>
              <div class="mt-2 space-y-2">
                @for (entry of group.entries; track entry.id) {
                  <app-qa-expandable-entry
                    [entry]="entry"
                    [expanded]="isExpanded(entry.id)"
                    [answer]="getAnswer(entry)"
                    [loadingAnswer]="isLoadingAnswer(entry.id)"
                    [showDayPrefix]="true"
                    [showDate]="false"
                    dateField="created_at"
                    (toggle)="toggleExpand($event)"
                  />
                }
              </div>
            </section>
          }
        </div>
        <app-list-paginator
          [total]="total"
          [pageSize]="pageSize"
          [currentPage]="currentPage"
          (pageChange)="setPage($event)"
        />
      }
    </div>
  `,
})
export class QAListComponent implements OnInit {
  private readonly qaService = inject(QAService);
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly viewTabs: ViewTab[] = [
    { id: 'all', label: 'All Q&A' },
    { id: 'month', label: 'By Month' },
    { id: 'deep', label: 'Deep Personal' },
  ];

  view: QAViewMode = 'all';
  entries: QAListItem[] = [];
  total = 0;
  loading = false;
  currentPage = 1;
  readonly pageSize = 20;
  readonly types = signal<string[]>([]);

  filters = this.fb.nonNullable.group({ search: '', type: '', tag: '' });

  private readonly expandedIds = new Set<string>();
  private readonly answerCache = new Map<string, string>();
  private readonly loadingAnswerIds = new Set<string>();

  ngOnInit(): void {
    this.qaService.listTypes().subscribe({ next: (t) => this.types.set(t) });
    this.route.queryParamMap.subscribe((params) => {
      const paramView = params.get('view');
      const nextView: QAViewMode =
        paramView === 'month' || paramView === 'deep' ? paramView : 'all';
      const viewChanged = nextView !== this.view;
      this.view = nextView;
      if (viewChanged) {
        this.currentPage = 1;
        this.expandedIds.clear();
      }
      this.load();
    });
  }

  get monthGroups() {
    return groupEntriesByMonth(this.entries);
  }

  get emptyMessage(): string {
    if (this.view === 'month') return 'No Q&A for this period.';
    if (this.view === 'deep') {
      return 'No deep personal questions yet. Mark a Q&A as Deep Personal when you want to track your more personal thinking.';
    }
    return 'No Q&A yet. Start capturing questions that come to mind.';
  }

  setView(view: QAViewMode): void {
    if (this.view === view) return;
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { view: view === 'all' ? null : view },
      queryParamsHandling: 'merge',
    });
  }

  applyFilters(): void {
    this.currentPage = 1;
    this.expandedIds.clear();
    this.load();
  }

  setPage(page: number): void {
    this.currentPage = page;
    this.expandedIds.clear();
    this.load();
  }

  load(): void {
    this.loading = true;
    const { search, type, tag } = this.filters.getRawValue();
    const offset = (this.currentPage - 1) * this.pageSize;
    this.qaService
      .list({
        search: search || undefined,
        type: type || undefined,
        tag: tag || undefined,
        deep_personal: this.view === 'deep' ? true : undefined,
        sort_by: this.view === 'all' ? 'updated_at' : 'created_at',
        limit: this.pageSize,
        offset,
        include_answer: false,
      })
      .subscribe({
        next: (result) => {
          this.entries = result.items;
          this.total = result.total;
          this.clampPage(result.total);
          this.loading = false;
        },
        error: () => (this.loading = false),
      });
  }

  isExpanded(id: string): boolean {
    return this.expandedIds.has(id);
  }

  isLoadingAnswer(id: string): boolean {
    return this.loadingAnswerIds.has(id);
  }

  getAnswer(entry: QAListItem): string {
    return this.answerCache.get(entry.id) ?? entry.current_answer ?? '';
  }

  toggleExpand(id: string): void {
    if (this.expandedIds.has(id)) {
      this.expandedIds.delete(id);
      return;
    }
    this.expandedIds.add(id);
    if (!this.answerCache.has(id)) {
      const cached = this.entries.find((e) => e.id === id)?.current_answer;
      if (cached) {
        this.answerCache.set(id, cached);
        return;
      }
      this.loadingAnswerIds.add(id);
      this.qaService.get(id).subscribe({
        next: (entry) => {
          this.answerCache.set(id, entry.current_answer);
          this.loadingAnswerIds.delete(id);
        },
        error: () => this.loadingAnswerIds.delete(id),
      });
    }
  }

  private clampPage(total: number): void {
    const totalPages = Math.max(1, Math.ceil(total / this.pageSize));
    if (this.currentPage > totalPages) {
      this.currentPage = totalPages;
      this.load();
    }
  }
}
