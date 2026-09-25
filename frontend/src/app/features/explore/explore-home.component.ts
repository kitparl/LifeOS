import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { EXPLORE_TOOLS, exploreToolRoute } from './explore-tools.registry';

@Component({
  selector: 'app-explore-home',
  standalone: true,
  imports: [RouterLink, LucideDynamicIcon],
  template: `
    <div class="space-y-3">
      <p class="text-sm text-[var(--text-muted)]">
        Free tools you can use without an account. Nothing you type is sent to a server.
      </p>
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        @for (tool of tools; track tool.id) {
          <div class="panel panel--flat flex flex-col gap-2" [attr.data-testid]="'explore-home-card-' + tool.id">
            <div class="flex min-w-0 items-center gap-2">
              <svg class="h-4 w-4 shrink-0 text-[var(--primary)]" [lucideIcon]="tool.icon" aria-hidden="true"></svg>
              <h2 class="truncate text-sm font-semibold">{{ tool.label }}</h2>
            </div>
            <p class="flex-1 text-xs text-[var(--text-muted)]">{{ tool.description }}</p>
            <a
              class="btn-primary self-start"
              [routerLink]="routeFor(tool)"
              [attr.data-testid]="'explore-home-open-' + tool.id"
            >Open</a>
          </div>
        }
      </div>
    </div>
  `,
})
export class ExploreHomeComponent {
  readonly tools = EXPLORE_TOOLS;
  readonly routeFor = exploreToolRoute;
}
