import { Component, Input, OnInit, Signal, inject, signal } from '@angular/core';
import { DevHistoryEntry, DevHistoryService, HISTORY_EXCLUDED_TOOL_IDS } from './dev-history.service';

@Component({
  selector: 'app-dev-history-panel',
  standalone: true,
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
                    <button type="button" class="btn-ghost" style="padding: 0.1rem 0.4rem" (click)="remove(entry.id!)">Delete</button>
                  </div>
                  <p class="truncate font-mono"><span class="text-[var(--text-muted)]">In:</span> {{ entry.input }}</p>
                  <p class="truncate font-mono"><span class="text-[var(--text-muted)]">Out:</span> {{ entry.output }}</p>
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

  private readonly historyService = inject(DevHistoryService);
  readonly expanded = signal(false);
  entries: Signal<DevHistoryEntry[]> = signal<DevHistoryEntry[]>([]);
  excluded = false;

  ngOnInit(): void {
    this.excluded = HISTORY_EXCLUDED_TOOL_IDS.has(this.toolId);
    if (!this.excluded) {
      this.entries = this.historyService.getHistory(this.toolId);
    }
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
