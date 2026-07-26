import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { FilesService } from '../files/services/files.service';
import { WishlistItem, wishlistStatusAccent, wishlistStatusBadge } from './models/wishlist.models';
import { WishlistService } from './services/wishlist.service';

@Component({
  selector: 'app-wishlist-detail',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    @if (item; as i) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 class="text-lg font-semibold">{{ i.title }}</h1>
            <p class="text-xs capitalize text-gray-600">{{ i.category }}</p>
          </div>
          <div class="flex gap-2">
            <a [routerLink]="['/wishlist', i.id, 'edit']" class="btn-primary text-xs no-underline">Edit</a>
            <button type="button" class="input-field !w-auto text-xs text-red-700" (click)="remove()">Delete</button>
          </div>
        </div>

        @if (imageSrcs.length) {
          <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
            @for (src of imageSrcs; track src; let idx = $index) {
              <img
                [src]="src"
                [alt]="i.title + ' ' + (idx + 1)"
                class="max-h-48 w-full object-cover border border-[var(--xp-border)]"
              />
            }
          </div>
        }

        <div
          class="panel text-sm space-y-2 border-l-4"
          [style.border-left-color]="statusAccent(i.status)"
          [style.background]="cardBackground(i.status)"
        >
          <p class="flex flex-wrap items-center gap-2">
            <span class="font-medium">Status:</span>
            <span [class]="statusBadge(i.status)">{{ statusLabel(i.status) }}</span>
          </p>
          <p><span class="font-medium">Priority:</span> {{ priorityLabel(i.priority) }}</p>
          @if (i.target_year) {
            <p><span class="font-medium">Target year:</span> {{ i.target_year }}</p>
          }
          @if (i.achieved_date) {
            <p><span class="font-medium">Achieved:</span> {{ i.achieved_date | date: 'mediumDate' }}</p>
          }
          @if (i.description) {
            <p class="whitespace-pre-wrap text-gray-700">{{ i.description }}</p>
          }
          @if (i.notes) {
            <p class="whitespace-pre-wrap text-gray-600 text-xs">{{ i.notes }}</p>
          }
        </div>

        <a routerLink="/wishlist" class="text-sm text-[var(--xp-blue)] underline">Back to wishlist</a>
      </div>
    } @else if (loading) {
      <p class="text-sm">Loading…</p>
    } @else {
      <p class="text-sm text-red-700">Not found.</p>
    }
  `,
})
export class WishlistDetailComponent implements OnInit {
  private readonly wishlistService = inject(WishlistService);
  private readonly filesService = inject(FilesService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  item: WishlistItem | null = null;
  loading = false;
  imageSrcs: string[] = [];

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loading = true;
      this.wishlistService.get(id).subscribe({
        next: (i) => {
          this.item = i;
          this.loading = false;
          this.resolveImages(i);
        },
        error: () => {
          this.item = null;
          this.loading = false;
        },
      });
    }
  }

  private resolveImages(item: WishlistItem): void {
    const urls = item.photos?.length ? item.photos : item.image_url ? [item.image_url] : [];
    for (const url of urls) {
      const fileId = url.match(/\/files\/([0-9a-f-]{36})\/content/i)?.[1];
      if (fileId) {
        this.filesService.tokenUrl(fileId).subscribe({
          next: (src) => {
            if (!this.imageSrcs.includes(src)) {
              this.imageSrcs = [...this.imageSrcs, src];
            }
          },
          error: () => {
            if (!this.imageSrcs.includes(url)) {
              this.imageSrcs = [...this.imageSrcs, url];
            }
          },
        });
      } else if (!this.imageSrcs.includes(url)) {
        this.imageSrcs = [...this.imageSrcs, url];
      }
    }
  }

  statusLabel(status: string): string {
    if (status === 'in_progress') return 'In progress';
    return status.charAt(0).toUpperCase() + status.slice(1);
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

  remove(): void {
    if (!this.item || !confirm('Delete this wishlist item?')) return;
    this.wishlistService.delete(this.item.id).subscribe({
      next: () => this.router.navigate(['/wishlist']),
    });
  }
}
