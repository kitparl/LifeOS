import { DatePipe } from '@angular/common';
import { Component, effect, inject, input, output, signal, untracked } from '@angular/core';
import { MarkdownEditorComponent } from '../../../shared/code-workspace/components/markdown-editor/markdown-editor.component';
import { ListPaginatorComponent } from '../../../shared/pagination/list-paginator.component';
import { PaginatedListState } from '../../../shared/pagination/paginated-list.state';
import { DsaLanguage, LANGUAGE_LABELS, SubmissionDetail, SubmissionSummary } from '../models/dsa.models';
import { DsaService } from '../services/dsa.service';
import { DsaStateComponent } from './dsa-state.component';
import { SubmissionResultComponent } from './submission-result.component';
import { VerdictBadgeComponent } from './verdict-badge.component';

const PAGE_SIZE = 10;

/** Past submissions for one problem; open one to read its code (read-only) or load it back. */
@Component({
  selector: 'app-dsa-submission-history',
  standalone: true,
  imports: [
    DatePipe,
    MarkdownEditorComponent,
    ListPaginatorComponent,
    DsaStateComponent,
    SubmissionResultComponent,
    VerdictBadgeComponent,
  ],
  template: `
    @if (selected(); as s) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-center gap-2">
          <button type="button" class="btn-ghost !min-h-8 !px-2 text-xs" data-testid="dsa-history-back-button" (click)="selected.set(null)">
            All submissions
          </button>
          <button
            type="button"
            class="btn-secondary !min-h-8 !px-2.5 text-xs"
            data-testid="dsa-history-load-button"
            (click)="loadCode.emit({ code: s.code, language: s.language })"
          >
            Load into editor
          </button>
        </div>
        <app-dsa-submission-result [submission]="s" />
        <div class="h-72 overflow-hidden rounded" style="border: 1px solid var(--border)">
          <app-markdown-editor [content]="s.code" [language]="s.language" [theme]="theme()" [readOnly]="true" />
        </div>
      </div>
    } @else if (error()) {
      <app-dsa-state title="We couldn't load your submissions." [retryable]="true" (retry)="load()" />
    } @else if (!loading() && items().length === 0) {
      <app-dsa-state title="No submissions yet" message="Submit a solution to see it here." />
    } @else {
      <ul class="divide-y text-sm" style="border-color: var(--border)">
        @for (s of items(); track s.id) {
          <li>
            <button
              type="button"
              class="flex w-full flex-wrap items-center gap-2 px-1 py-2 text-left hover:bg-[var(--surface-2)]"
              [attr.data-testid]="'dsa-history-row-' + s.id"
              (click)="open(s)"
            >
              <app-dsa-verdict-badge [verdict]="s.verdict" />
              <span class="text-xs" style="color: var(--text-muted)">{{ languages[s.language] }}</span>
              @if (s.runtime_ms !== null) {
                <span class="text-xs" style="color: var(--text-muted)">{{ s.runtime_ms }} ms</span>
              }
              <span class="ml-auto text-xs" style="color: var(--text-muted)">{{ s.created_at | date: 'medium' }}</span>
            </button>
          </li>
        }
      </ul>
      <app-list-paginator [total]="page.total" [pageSize]="page.pageSize" [currentPage]="page.currentPage" (pageChange)="goTo($event)" />
    }
  `,
})
export class SubmissionHistoryComponent {
  private readonly dsa = inject(DsaService);

  readonly slug = input.required<string>();
  /** Bump to reload (e.g. after a new submission). */
  readonly refresh = input(0);
  readonly theme = input<'light' | 'dark'>('light');
  readonly loadCode = output<{ code: string; language: DsaLanguage }>();

  readonly languages = LANGUAGE_LABELS;
  readonly page = new PaginatedListState(PAGE_SIZE);
  readonly items = signal<SubmissionSummary[]>([]);
  readonly selected = signal<SubmissionDetail | null>(null);
  readonly loading = signal(false);
  readonly error = signal(false);

  constructor() {
    effect(() => {
      this.refresh();
      this.slug();
      untracked(() => {
        this.page.setPage(1);
        this.selected.set(null);
        this.load();
      });
    });
  }

  load(): void {
    this.loading.set(true);
    this.error.set(false);
    this.dsa.history(this.slug(), this.page.pageSize, this.page.offset).subscribe({
      next: (res) => {
        this.items.set(res.items);
        this.page.total = res.total;
        this.loading.set(false);
      },
      error: () => {
        this.error.set(true);
        this.loading.set(false);
      },
    });
  }

  goTo(page: number): void {
    this.page.setPage(page);
    this.load();
  }

  open(summary: SubmissionSummary): void {
    this.dsa.submission(summary.id).subscribe({
      next: (detail) => this.selected.set(detail),
      error: () => this.error.set(true),
    });
  }
}
