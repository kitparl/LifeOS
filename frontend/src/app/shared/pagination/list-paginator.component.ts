import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-list-paginator',
  standalone: true,
  template: `
    @if (totalPages > 1) {
      <div
        class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
        role="navigation"
        aria-label="Pagination"
        style="padding: 0.625rem 1rem; border-top: 1px solid var(--border); background: var(--surface-2)"
      >
        <span class="text-xs" style="color: var(--text-muted)">
          @if (total > 0) {
            Showing {{ startItem }}–{{ endItem }} of {{ total }}
          }
        </span>
        <div class="flex items-center gap-1.5">
          <button
            type="button"
            class="btn-secondary !min-h-8 !px-2.5 text-xs"
            [disabled]="currentPage <= 1"
            (click)="goTo(1)"
            (keydown.enter)="goTo(1)"
            aria-label="First page"
          >
            «
          </button>
          <button
            type="button"
            class="btn-secondary !min-h-8 !px-3 text-xs"
            [disabled]="currentPage <= 1"
            (click)="goTo(currentPage - 1)"
            (keydown.enter)="goTo(currentPage - 1)"
            aria-label="Previous page"
          >
            Prev
          </button>

          <!-- Page number buttons (up to 5 visible) -->
          @for (page of visiblePages; track page) {
            @if (page === -1) {
              <span class="text-xs px-1" style="color: var(--text-faint)">…</span>
            } @else {
              <button
                type="button"
                class="btn-ghost !min-h-8 !px-2.5 text-xs"
                [class.btn-primary]="page === currentPage"
                (click)="goTo(page)"
                [attr.aria-label]="'Page ' + page"
                [attr.aria-current]="page === currentPage ? 'page' : null"
              >
                {{ page }}
              </button>
            }
          }

          <button
            type="button"
            class="btn-secondary !min-h-8 !px-3 text-xs"
            [disabled]="currentPage >= totalPages"
            (click)="goTo(currentPage + 1)"
            (keydown.enter)="goTo(currentPage + 1)"
            aria-label="Next page"
          >
            Next
          </button>
          <button
            type="button"
            class="btn-secondary !min-h-8 !px-2.5 text-xs"
            [disabled]="currentPage >= totalPages"
            (click)="goTo(totalPages)"
            (keydown.enter)="goTo(totalPages)"
            aria-label="Last page"
          >
            »
          </button>
        </div>
      </div>
    }
  `,
})
export class ListPaginatorComponent {
  @Input() total = 0;
  @Input() pageSize = 12;
  @Input() currentPage = 1;
  @Output() pageChange = new EventEmitter<number>();

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.total / this.pageSize));
  }

  get startItem(): number {
    return this.total === 0 ? 0 : (this.currentPage - 1) * this.pageSize + 1;
  }

  get endItem(): number {
    return Math.min(this.total, this.currentPage * this.pageSize);
  }

  get visiblePages(): number[] {
    const total = this.totalPages;
    const current = this.currentPage;
    if (total <= 7) {
      return Array.from({ length: total }, (_, i) => i + 1);
    }
    const pages: number[] = [1];
    if (current > 3) pages.push(-1); // ellipsis
    for (let p = Math.max(2, current - 1); p <= Math.min(total - 1, current + 1); p++) {
      pages.push(p);
    }
    if (current < total - 2) pages.push(-1); // ellipsis
    pages.push(total);
    return pages;
  }

  goTo(page: number): void {
    const nextPage = Math.min(Math.max(page, 1), this.totalPages);
    if (nextPage !== this.currentPage) {
      this.pageChange.emit(nextPage);
    }
  }
}
