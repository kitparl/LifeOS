import { Component, computed, inject, signal } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { LucideDynamicIcon } from '@lucide/angular';
import { DEV_TOOL_CATEGORIES } from './data/dev-tool-categories';
import { DEV_TOOLS } from './data/dev-tools-registry';
import { DevToolMeta } from './models/dev-tool.model';
import { DevFavoritesService } from './shared/dev-favorites.service';

@Component({
  selector: 'app-developer-dashboard',
  standalone: true,
  imports: [RouterLink, FormsModule, LucideDynamicIcon, NgTemplateOutlet],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <p class="text-sm text-[var(--text-muted)]">
          Fast client-side utilities. Nothing you type here is stored or sent to a server.
        </p>
        <div class="relative w-full max-w-md">
          <svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-faint)]" lucideIcon="search" aria-hidden="true"></svg>
          <input
            class="input-field"
            style="padding-left: 2.5rem"
            type="text"
            placeholder="Search tools by name, category, or keyword…"
            [ngModel]="query()"
            (ngModelChange)="query.set($event)"
          />
        </div>
      </div>

      @if (!query() && favoriteTools().length) {
        <section>
          <h2 class="mb-2 flex items-center gap-2 text-sm font-semibold">
            <svg class="star-favorite h-4 w-4" lucideIcon="star" fill="currentColor" aria-hidden="true"></svg>
            Favorites
          </h2>
          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            @for (tool of favoriteTools(); track tool.id) {
              <ng-container [ngTemplateOutlet]="toolCard" [ngTemplateOutletContext]="{ tool }" />
            }
          </div>
        </section>
      }

      @if (query() && filteredTools().length === 0) {
        <p class="text-sm text-[var(--text-muted)]">No tools match "{{ query() }}".</p>
      }

      @for (category of categories; track category.id) {
        @if (toolsByCategory(category.id).length) {
          <section>
            <h2 class="mb-2 flex items-center gap-2 text-sm font-semibold">
              <svg class="h-4 w-4 text-[var(--primary)]" [lucideIcon]="category.icon" aria-hidden="true"></svg>
              {{ category.label }}
              <span class="text-xs font-normal text-[var(--text-muted)]">{{ category.description }}</span>
            </h2>
            <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              @for (tool of toolsByCategory(category.id); track tool.id) {
                <ng-container [ngTemplateOutlet]="toolCard" [ngTemplateOutletContext]="{ tool }" />
              }
            </div>
          </section>
        }
      }
    </div>

    <ng-template #toolCard let-tool="tool">
      <div class="panel panel--flat flex flex-col gap-2">
        <div class="flex items-start justify-between gap-2">
          <div class="flex min-w-0 items-center gap-2">
            <svg class="h-4 w-4 shrink-0 text-[var(--primary)]" [lucideIcon]="tool.icon" aria-hidden="true"></svg>
            <h3 class="truncate text-sm font-semibold">{{ tool.name }}</h3>
          </div>
          <button
            type="button"
            class="btn-ghost shrink-0"
            style="padding: 0.2rem"
            [class.star-favorite]="isFavorite(tool.id)"
            [attr.aria-pressed]="isFavorite(tool.id)"
            [attr.aria-label]="isFavorite(tool.id) ? 'Unfavorite' : 'Favorite'"
            (click)="toggleFavorite(tool.id)"
          >
            <svg
              class="h-4 w-4"
              [class.star-favorite]="isFavorite(tool.id)"
              lucideIcon="star"
              [color]="isFavorite(tool.id) ? 'var(--favorite)' : 'currentColor'"
              aria-hidden="true"
            ></svg>
          </button>
        </div>
        <p class="flex-1 text-xs text-[var(--text-muted)]">{{ tool.description }}</p>
        <a class="btn-primary self-start" [routerLink]="[tool.route]">Open</a>
      </div>
    </ng-template>
  `,
})
export class DeveloperDashboardComponent {
  private readonly favoritesService = inject(DevFavoritesService);

  readonly categories = DEV_TOOL_CATEGORIES;
  readonly query = signal('');

  readonly filteredTools = computed<DevToolMeta[]>(() => {
    const q = this.query().trim().toLowerCase();
    if (!q) return DEV_TOOLS;
    return DEV_TOOLS.filter(
      (tool) =>
        tool.name.toLowerCase().includes(q) ||
        tool.description.toLowerCase().includes(q) ||
        tool.categories.some((catId) => this.categoryLabel(catId).toLowerCase().includes(q)) ||
        tool.keywords.some((keyword) => keyword.toLowerCase().includes(q)),
    );
  });

  readonly favoriteTools = computed<DevToolMeta[]>(() =>
    DEV_TOOLS.filter((tool) => this.favoritesService.isFavorite(tool.id)),
  );

  toolsByCategory(categoryId: string): DevToolMeta[] {
    return this.filteredTools().filter((tool) => tool.categories.includes(categoryId));
  }

  categoryLabel(categoryId: string): string {
    return DEV_TOOL_CATEGORIES.find((c) => c.id === categoryId)?.label ?? categoryId;
  }

  isFavorite(toolId: string): boolean {
    return this.favoritesService.isFavorite(toolId);
  }

  toggleFavorite(toolId: string): void {
    this.favoritesService.toggle(toolId);
  }
}
