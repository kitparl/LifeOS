import { Component, computed, input } from '@angular/core';

/** Placeholder cards/rows while news loads (no blank screens). */
@Component({
  selector: 'app-news-skeleton',
  standalone: true,
  template: `
    <div [class]="layout() === 'grid' ? 'grid gap-3 sm:grid-cols-2 xl:grid-cols-3' : 'space-y-2'" aria-hidden="true">
      @for (i of slots(); track i) {
        @if (layout() === 'grid') {
          <div class="panel--flat !p-0 overflow-hidden">
            <div class="skeleton aspect-video w-full !rounded-none"></div>
            <div class="space-y-2 p-3">
              <div class="skeleton-text w-11/12"></div>
              <div class="skeleton-text w-8/12"></div>
              <div class="skeleton-text w-5/12"></div>
            </div>
          </div>
        } @else {
          <div class="panel--flat flex gap-3 !p-3">
            <div class="skeleton h-16 w-24 shrink-0"></div>
            <div class="flex-1 space-y-2">
              <div class="skeleton-text w-10/12"></div>
              <div class="skeleton-text w-6/12"></div>
              <div class="skeleton-text w-4/12"></div>
            </div>
          </div>
        }
      }
    </div>
    <span class="sr-only" role="status">Loading…</span>
  `,
})
export class NewsSkeletonComponent {
  readonly layout = input<'grid' | 'rows'>('grid');
  readonly count = input(6);
  readonly slots = computed(() => Array.from({ length: this.count() }, (_, i) => i));
}
