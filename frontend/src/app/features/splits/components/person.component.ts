import { Component, computed, input } from '@angular/core';

/** A contributor: initial badge + name, with an optional "you" tag. Used wherever a split shows a person. */
@Component({
  selector: 'app-split-person',
  standalone: true,
  host: { class: 'inline-flex min-w-0 items-center gap-1.5 align-middle' },
  template: `
    <span
      class="grid shrink-0 place-items-center rounded-full font-semibold text-white"
      [class.h-5]="size() === 'sm'"
      [class.w-5]="size() === 'sm'"
      [class.text-[10px]]="size() === 'sm'"
      [class.h-7]="size() === 'md'"
      [class.w-7]="size() === 'md'"
      [class.text-xs]="size() === 'md'"
      style="background: var(--primary)"
      aria-hidden="true"
    >{{ initial() }}</span>
    <span class="truncate font-semibold" style="color: var(--text)" data-testid="split-person-name">{{ name() }}</span>
    @if (you()) {
      <span class="shrink-0 rounded-full px-1.5 text-[10px] font-medium" style="background: var(--xp-border); color: var(--text)">you</span>
    }
  `,
})
export class SplitPersonComponent {
  readonly name = input.required<string>();
  readonly you = input(false);
  readonly size = input<'sm' | 'md'>('sm');

  readonly initial = computed(() => this.name().trim().charAt(0).toUpperCase() || '?');
}
