import { Component, EventEmitter, Input, OnInit, Output, Signal, inject, signal } from '@angular/core';
import { DevHistoryEntry, DevHistoryService, HISTORY_EXCLUDED_TOOL_IDS } from './dev-history.service';
import { CopyButtonComponent } from './copy-button.component';

@Component({
  selector: 'app-dev-history-panel',
  standalone: true,
  imports: [CopyButtonComponent],
  template: `
    @if (!excluded) {
      <div class="mt-6 border-t border-[var(--border)] pt-3">
        <button type="button" class="btn-ghost" (click)="expanded.set(!expanded())">
          History ({{ entries().length }}) {{ expanded() ? '▲' : '▼' }}
        </button>
        @if (expanded()) {
          @if (entries().length === 0) {
            <p class="mt-2 text-sm text-[var(--text-muted)]">
              No history yet — kept locally in your browser for 30 days, then cleared automatically.
            </p>
          } @else {
            <div class="mb-2 mt-2 flex items-center justify-between">
              <p class="text-xs text-[var(--text-muted)]">Kept locally for 30 days, then cleared automatically.</p>
              <button type="button" class="btn-ghost" (click)="clear()">Clear history</button>
            </div>
            <ul class="max-h-72 space-y-2 overflow-auto">
              @for (entry of entries(); track entry.id) {
                <li class="rounded-[var(--radius-sm)] border border-[var(--border)] p-2 text-xs">
                  <div class="mb-1 flex items-center justify-between text-[var(--text-muted)]">
                    <span>{{ formatDate(entry.createdAt) }}</span>
                    <div class="flex items-center gap-1">
                      <button type="button" class="btn-ghost" style="padding: 0.1rem 0.4rem" (click)="use(entry)">
                        Use
                      </button>
                      <button
                        type="button"
                        class="btn-ghost"
                        style="padding: 0.1rem 0.4rem"
                        [attr.aria-expanded]="isExpanded(entry.id!)"
                        (click)="toggleView(entry.id!)"
                      >
                        {{ isExpanded(entry.id!) ? 'Hide' : 'View' }}
                      </button>
                      <button type="button" class="btn-ghost" style="padding: 0.1rem 0.4rem" (click)="remove(entry.id!)">
                        Delete
                      </button>
                    </div>
                  </div>
                  <p class="truncate font-mono"><span class="text-[var(--text-muted)]">In:</span> {{ entry.input }}</p>
                  <p class="truncate font-mono"><span class="text-[var(--text-muted)]">Out:</span> {{ entry.output }}</p>

                  @if (isExpanded(entry.id!)) {
                    <div class="mt-2 space-y-2 border-t border-[var(--border)] pt-2">
                      <div class="space-y-1">
                        <div class="flex items-center justify-between">
                          <span class="text-[var(--text-muted)]">Full input</span>
                          <app-copy-button [text]="entry.input" label="Copy In" />
                        </div>
                        <textarea
                          class="input-field h-24 w-full resize-y overflow-auto font-mono text-xs"
                          readonly
                          [value]="entry.input"
                        ></textarea>
                      </div>
                      <div class="space-y-1">
                        <div class="flex items-center justify-between">
                          <span class="text-[var(--text-muted)]">Full output</span>
                          <app-copy-button [text]="entry.output" label="Copy Out" />
                        </div>
                        <textarea
                          class="input-field h-24 w-full resize-y overflow-auto font-mono text-xs"
                          readonly
                          [value]="entry.output"
                        ></textarea>
                      </div>
                      <button type="button" class="btn-secondary" (click)="use(entry)">Use in tool</button>
                    </div>
                  }
                </li>
              }
            </ul>
          }
        }
      </div>
    }
  `,
})
export class DevHistoryPanelComponent implements OnInit {
  @Input({ required: true }) toolId = '';

  /** Emitted when "Use" / "Use in tool" is clicked, so the owning tool shell can reload this entry. */
  @Output() readonly reuse = new EventEmitter<DevHistoryEntry>();

  private readonly historyService = inject(DevHistoryService);
  readonly expanded = signal(false);
  private readonly expandedIds = signal<ReadonlySet<number>>(new Set());
  entries: Signal<DevHistoryEntry[]> = signal<DevHistoryEntry[]>([]);
  excluded = false;

  ngOnInit(): void {
    this.excluded = HISTORY_EXCLUDED_TOOL_IDS.has(this.toolId);
    if (!this.excluded) {
      this.entries = this.historyService.getHistory(this.toolId);
    }
  }

  isExpanded(id: number): boolean {
    return this.expandedIds().has(id);
  }

  toggleView(id: number): void {
    const next = new Set(this.expandedIds());
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    this.expandedIds.set(next);
  }

  use(entry: DevHistoryEntry): void {
    this.reuse.emit(entry);
  }

  remove(id: number): void {
    void this.historyService.deleteEntry(this.toolId, id);
  }

  clear(): void {
    void this.historyService.clearHistory(this.toolId);
  }

  formatDate(iso: string): string {
    return new Date(iso).toLocaleString();
  }
}
