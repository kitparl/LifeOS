import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { parseJsonOrThrow } from './json.util';
import { diffJson, JsonDiffEntry } from './json-diff.util';

@Component({
  selector: 'app-json-diff-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell toolId="json-diff" title="JSON Diff" description="Compare two JSON objects and see what changed." icon="diff">
      <div class="grid gap-3 pb-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">Left (original)</label>
          <textarea
            class="input-field h-48 resize-y font-mono text-sm"
            placeholder='{"a": 1}'
            [ngModel]="left()"
            (ngModelChange)="setLeft($event)"
          ></textarea>
        </div>
        <div class="space-y-1">
          <label class="form-label">Right (changed)</label>
          <textarea
            class="input-field h-48 resize-y font-mono text-sm"
            placeholder='{"a": 2}'
            [ngModel]="right()"
            (ngModelChange)="setRight($event)"
          ></textarea>
        </div>
      </div>

      @if (error()) {
        <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
      } @else if (entries().length === 0 && left() && right()) {
        <p class="text-sm text-[var(--success)]">No differences.</p>
      } @else if (entries().length) {
        <div class="flex items-center justify-between pb-2">
          <p class="text-sm text-[var(--text-muted)]">{{ entries().length }} difference(s)</p>
          <app-copy-button [text]="summaryText()" label="Copy summary" />
        </div>
        <ul class="space-y-1.5">
          @for (entry of entries(); track entry.path) {
            <li class="flex flex-wrap items-baseline gap-2 rounded-[var(--radius-sm)] border border-[var(--border)] px-2.5 py-1.5 text-xs">
              <span
                class="badge shrink-0"
                [style.background]="badgeBg(entry.type)"
                [style.color]="badgeColor(entry.type)"
              >
                {{ entry.type }}
              </span>
              <code class="font-mono">{{ entry.path }}</code>
              @if (entry.type !== 'added') {
                <span class="text-[var(--danger)] line-through">{{ stringify(entry.oldValue) }}</span>
              }
              @if (entry.type !== 'removed') {
                <span class="text-[var(--success)]">{{ stringify(entry.newValue) }}</span>
              }
            </li>
          }
        </ul>
      }
    </app-dev-tool-shell>
  `,
})
export class JsonDiffToolComponent {
  readonly left = signal('');
  readonly right = signal('');
  readonly error = signal<string | null>(null);
  readonly entries = signal<JsonDiffEntry[]>([]);

  readonly summaryText = computed(() =>
    this.entries()
      .map((e) => `${e.type.toUpperCase()} ${e.path}: ${this.stringify(e.oldValue)} -> ${this.stringify(e.newValue)}`)
      .join('\n'),
  );

  setLeft(value: string): void {
    this.left.set(value);
    this.run();
  }

  setRight(value: string): void {
    this.right.set(value);
    this.run();
  }

  stringify(value: unknown): string {
    return value === undefined ? '—' : JSON.stringify(value);
  }

  badgeBg(type: JsonDiffEntry['type']): string {
    return type === 'added' ? 'var(--success-soft)' : type === 'removed' ? 'var(--danger-soft)' : 'var(--warning-soft)';
  }

  badgeColor(type: JsonDiffEntry['type']): string {
    return type === 'added' ? 'var(--success)' : type === 'removed' ? 'var(--danger)' : 'var(--warning)';
  }

  private run(): void {
    if (!this.left().trim() || !this.right().trim()) {
      this.entries.set([]);
      this.error.set(null);
      return;
    }
    try {
      const a = parseJsonOrThrow(this.left());
      const b = parseJsonOrThrow(this.right());
      this.entries.set(diffJson(a, b));
      this.error.set(null);
    } catch (e) {
      this.entries.set([]);
      this.error.set(e instanceof Error ? e.message : String(e));
    }
  }
}
