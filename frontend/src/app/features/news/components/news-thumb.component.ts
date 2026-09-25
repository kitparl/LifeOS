import { Component, input, signal } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';

/** Article image with lazy loading; a neutral placeholder when missing or broken. */
@Component({
  selector: 'app-news-thumb',
  standalone: true,
  imports: [LucideDynamicIcon],
  host: { class: 'block overflow-hidden', style: 'background: var(--surface-2)' },
  template: `
    @if (src() && !failed()) {
      <img
        class="h-full w-full object-cover"
        [src]="src()"
        [alt]="alt()"
        loading="lazy"
        decoding="async"
        referrerpolicy="no-referrer"
        (error)="failed.set(true)"
      />
    } @else {
      <div class="flex h-full w-full items-center justify-center" style="color: var(--text-faint)">
        <svg class="h-6 w-6" lucideIcon="newspaper" aria-hidden="true"></svg>
      </div>
    }
  `,
})
export class NewsThumbComponent {
  readonly src = input<string | null>(null);
  readonly alt = input('');
  readonly failed = signal(false);
}
