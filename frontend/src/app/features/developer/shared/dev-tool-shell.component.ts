import { Component, Input, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { DevFavoritesService } from './dev-favorites.service';

@Component({
  selector: 'app-dev-tool-shell',
  standalone: true,
  imports: [RouterLink, LucideDynamicIcon],
  template: `
    <div class="space-y-4">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div class="min-w-0">
          <a routerLink=".." class="text-xs text-[var(--text-muted)] hover:text-[var(--text)] no-underline">
            &larr; Developer
          </a>
          <h1 class="mt-1 flex items-center gap-2 text-lg font-semibold">
            @if (icon) {
              <svg class="h-5 w-5 shrink-0 text-[var(--primary)]" [lucideIcon]="icon" aria-hidden="true"></svg>
            }
            {{ title }}
          </h1>
          <p class="text-sm text-[var(--text-muted)]">{{ description }}</p>
        </div>
        @if (toolId) {
          <button
            type="button"
            class="btn-ghost shrink-0"
            [class.star-favorite]="favorites.isFavorite(toolId)"
            [attr.aria-pressed]="favorites.isFavorite(toolId)"
            (click)="favorites.toggle(toolId)"
          >
            <svg
              class="h-4 w-4"
              [class.star-favorite]="favorites.isFavorite(toolId)"
              lucideIcon="star"
              [color]="favorites.isFavorite(toolId) ? 'var(--favorite)' : 'currentColor'"
              aria-hidden="true"
            ></svg>
            {{ favorites.isFavorite(toolId) ? 'Favorited' : 'Favorite' }}
          </button>
        }
      </div>
      <div class="panel">
        <ng-content />
      </div>
    </div>
  `,
})
export class DevToolShellComponent {
  @Input({ required: true }) title = '';
  @Input({ required: true }) description = '';
  @Input() icon = '';
  @Input() toolId = '';

  readonly favorites = inject(DevFavoritesService);
}
