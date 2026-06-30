import { DecimalPipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { WISHLIST_CATEGORIES, WishlistListItem } from './models/wishlist.models';
import { WishlistService } from './services/wishlist.service';

@Component({
  selector: 'app-wishlist-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DecimalPipe],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Wishlist</h1>
        <a routerLink="/wishlist/new" class="btn-primary text-xs no-underline">New Item</a>
      </div>

      <form class="flex gap-2 text-sm" [formGroup]="filters" (ngSubmit)="load()">
        <select class="input-field !w-auto" formControlName="category">
          <option value="">All categories</option>
          @for (c of categories; track c.value) {
            <option [value]="c.value">{{ c.label }}</option>
          }
        </select>
        <button type="submit" class="btn-primary text-xs">Filter</button>
      </form>

      @if (loading) {
        <p class="text-sm text-gray-600">Loading…</p>
      } @else if (items.length === 0) {
        <div class="panel">
          <p class="text-sm text-gray-600">Your bucket list is empty.</p>
          <a routerLink="/wishlist/new" class="btn-primary mt-2 inline-block text-xs no-underline">Add dream</a>
        </div>
      } @else {
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          @for (item of items; track item.id) {
            <div class="panel text-sm space-y-2">
              <a [routerLink]="['/wishlist', item.id]" class="font-medium text-[var(--xp-blue)] underline">{{ item.title }}</a>
              <p class="text-xs capitalize text-gray-600">{{ item.category }}</p>
              @if (item.cost) {
                <p class="text-xs">Est. cost: {{ item.cost | number }}</p>
              }
              <div class="h-2 bg-gray-200 border border-[var(--xp-border)]">
                <div class="h-full bg-[var(--xp-blue)]" [style.width.%]="item.progress"></div>
              </div>
              <p class="text-xs text-gray-600">{{ item.progress }}% progress</p>
            </div>
          }
        </div>
      }
    </div>
  `,
})
export class WishlistListComponent implements OnInit {
  private readonly wishlistService = inject(WishlistService);
  private readonly fb = inject(FormBuilder);

  categories = WISHLIST_CATEGORIES;
  items: WishlistListItem[] = [];
  loading = false;
  filters = this.fb.nonNullable.group({ category: '' });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    const category = this.filters.getRawValue().category;
    this.wishlistService.list(category || undefined).subscribe({
      next: (data) => {
        this.items = data;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}
