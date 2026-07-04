import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-list-paginator',
  standalone: true,
  template: `
    @if (total > pageSize) {
      <div class="flex flex-col gap-2 border-t border-[var(--xp-border)] px-3 py-2 text-xs text-[var(--text-muted)] sm:flex-row sm:items-center sm:justify-between">
        <span>
          Showing {{ startItem }}-{{ endItem }} of {{ total }}
        </span>
        <div class="flex items-center gap-2">
          <button type="button" class="input-field !min-h-9 !w-auto px-3 text-xs" [disabled]="currentPage <= 1" (click)="goTo(currentPage - 1)">
            Prev
          </button>
          <span class="rounded-lg border border-[var(--xp-border)] bg-[var(--surface)] px-3 py-2">
            Page {{ currentPage }} / {{ totalPages }}
          </span>
          <button type="button" class="input-field !min-h-9 !w-auto px-3 text-xs" [disabled]="currentPage >= totalPages" (click)="goTo(currentPage + 1)">
            Next
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

  goTo(page: number): void {
    const nextPage = Math.min(Math.max(page, 1), this.totalPages);
    if (nextPage !== this.currentPage) {
      this.pageChange.emit(nextPage);
    }
  }
}
