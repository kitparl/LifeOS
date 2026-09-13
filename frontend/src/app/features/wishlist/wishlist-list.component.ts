import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ListPaginatorComponent } from '../../shared/pagination/list-paginator.component';
import {
  WISHLIST_STATUS_FILTERS,
  WishlistListItem,
  WishlistStatusFilter,
  wishlistStatusAccent,
  wishlistStatusBadge,
} from './models/wishlist.models';
import { WishlistService } from './services/wishlist.service';

@Component({
  selector: 'app-wishlist-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe, ListPaginatorComponent],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Wishlist</h1>
        <a routerLink="/wishlist/new" class="btn-primary text-xs no-underline">New Item</a>
      </div>

      <form class="flex flex-wrap gap-2 text-sm" [formGroup]="filters" (ngSubmit)="applyFilters()">
        <select class="input-field !w-auto" formControlName="status">
          @for (s of statusFilters; track s.value) {
            <option [value]="s.value">{{ s.label }}</option>
          }
        </select>
        <select class="input-field !w-auto" formControlName="category">
          <option value="">All categories</option>
          @for (c of categories(); track c) {
            <option [value]="c">{{ c }}</option>
          }
        </select>
        <button type="submit" class="btn-primary text-xs">Filter</button>
      </form>

      @if (loading) {
        <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
      } @else if (total === 0) {
        <div class="panel">
          <p class="text-sm" style="color: var(--text-muted)">
            {{ emptyMessage }}
          </p>
          <a routerLink="/wishlist/new" class="btn-primary mt-2 inline-block text-xs no-underline">Add dream</a>
        </div>
      } @else {
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          @for (item of items; track item.id) {
            <div
              class="panel text-sm space-y-2 border-l-4"
              [style.border-left-color]="statusAccent(item.status)"
              [style.background]="cardBackground(item.status)"
            >
              <div class="flex flex-wrap items-start justify-between gap-2">
                <a [routerLink]="['/wishlist', item.id]" class="font-medium text-[var(--xp-blue)] underline">
                  {{ item.title }}
                </a>
                <span [class]="statusBadge(item.status)">{{ statusLabel(item.status) }}</span>
              </div>
              <p class="text-xs capitalize" style="color: var(--text-muted)">
                {{ item.category }} · {{ priorityLabel(item.priority) }}
              </p>
              @if (item.target_year) {
                <p class="text-xs">Target: {{ item.target_year }}</p>
              }
              @if (item.achieved_date) {
                <p class="text-xs" style="color: var(--text-muted)">Achieved {{ item.achieved_date | date: 'mediumDate' }}</p>
              }
            </div>
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
export class WishlistListComponent implements OnInit {
  private readonly wishlistService = inject(WishlistService);
  private readonly fb = inject(FormBuilder);

  readonly categories = signal<string[]>([]);
  readonly statusFilters = WISHLIST_STATUS_FILTERS;
  items: WishlistListItem[] = [];
  total = 0;
  loading = false;
  currentPage = 1;
  readonly pageSize = 25;
  filters = this.fb.nonNullable.group({
    status: '' as WishlistStatusFilter,
    category: '',
  });

  ngOnInit(): void {
    this.wishlistService.listCategories().subscribe({ next: (c) => this.categories.set(c) });
    this.load();
  }

  get emptyMessage(): string {
    const status = this.filters.getRawValue().status;
    if (status === 'incomplete') return 'No incomplete wishlist items.';
    if (status === 'completed') return 'No completed items yet.';
    if (status === 'delayed') return 'No delayed items.';
    if (status === 'in_progress') return 'No items in progress.';
    return 'Your bucket list is empty.';
  }

  statusLabel(status: string): string {
    if (status === 'in_progress') return 'In progress';
    return status.replace('_', ' ');
  }

  statusBadge(status: string): string {
    return wishlistStatusBadge(status);
  }

  statusAccent(status: string): string {
    return wishlistStatusAccent(status);
  }

  cardBackground(status: string): string {
    switch (status) {
      case 'completed':
        return 'color-mix(in srgb, var(--success-soft) 70%, var(--surface))';
      case 'delayed':
        return 'color-mix(in srgb, var(--warning-soft) 70%, var(--surface))';
      case 'in_progress':
        return 'color-mix(in srgb, var(--info-soft) 70%, var(--surface))';
      default:
        return 'var(--surface)';
    }
  }

  priorityLabel(priority: string): string {
    return priority.charAt(0).toUpperCase() + priority.slice(1);
  }

  applyFilters(): void {
    this.currentPage = 1;
    this.load();
  }

  load(): void {
    this.loading = true;
    const { category, status } = this.filters.getRawValue();
    const offset = (this.currentPage - 1) * this.pageSize;
    this.wishlistService
      .list({
        category: category || undefined,
        status: status || undefined,
        limit: this.pageSize,
        offset,
      })
      .subscribe({
        next: (result) => {
          this.items = result.items;
          this.total = result.total;
          this.clampPage();
          this.loading = false;
        },
        error: () => (this.loading = false),
      });
  }

  setPage(page: number): void {
    this.currentPage = page;
    this.load();
  }

  private clampPage(): void {
    const totalPages = Math.max(1, Math.ceil(this.total / this.pageSize));
    if (this.currentPage > totalPages) {
      this.currentPage = totalPages;
      this.load();
    }
  }
}
