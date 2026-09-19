import { Component, EventEmitter, Input, Output } from '@angular/core';

export interface TabHubItem {
  id: string;
  label: string;
}

@Component({
  selector: 'app-tab-hub',
  standalone: true,
  template: `
    <div class="flex flex-wrap items-end justify-between gap-2 border-b border-[var(--xp-border)] text-sm">
      <div class="flex min-w-0 gap-1" [class.flex-wrap]="wrap">
        @for (t of tabs; track t.id) {
          <button
            type="button"
            class="px-3 py-2"
            [class.bg-[var(--xp-blue)]]="activeId === t.id"
            [class.text-white]="activeId === t.id"
            (click)="tabChange.emit(t.id)"
          >
            {{ t.label }}
          </button>
        }
      </div>
      <div class="shrink-0">
        <ng-content />
      </div>
    </div>
  `,
})
export class TabHubComponent {
  @Input({ required: true }) tabs: TabHubItem[] = [];
  @Input({ required: true }) activeId = '';
  @Input() wrap = false;
  @Output() readonly tabChange = new EventEmitter<string>();
}
