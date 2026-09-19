import { Component, Input, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { computeDiffRows, toUnifiedDiff } from './diff.util';

@Component({
  selector: 'app-diff-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell [toolId]="toolId" [title]="title" [description]="description" icon="diff">
      <div class="grid gap-3 pb-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">Original</label>
          <textarea
            class="input-field h-56 resize-y font-mono text-sm"
            [ngModel]="left()"
            (ngModelChange)="left.set($event)"
          ></textarea>
        </div>
        <div class="space-y-1">
          <label class="form-label">Changed</label>
          <textarea
            class="input-field h-56 resize-y font-mono text-sm"
            [ngModel]="right()"
            (ngModelChange)="right.set($event)"
          ></textarea>
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-2 pb-2">
        <div class="inline-flex overflow-hidden rounded-[var(--radius-sm)] border border-[var(--border)]">
          <button type="button" class="px-3 py-1.5 text-sm" [style.background]="view() === 'side' ? 'var(--primary)' : 'transparent'" [style.color]="view() === 'side' ? '#fff' : 'var(--text)'" (click)="view.set('side')">Side-by-side</button>
          <button type="button" class="px-3 py-1.5 text-sm border-l border-[var(--border)]" [style.background]="view() === 'unified' ? 'var(--primary)' : 'transparent'" [style.color]="view() === 'unified' ? '#fff' : 'var(--text)'" (click)="view.set('unified')">Unified</button>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs text-[var(--text-muted)]">
            <span style="color: var(--success)">+{{ addedCount() }}</span>
            <span style="color: var(--danger)"> -{{ removedCount() }}</span>
            <span style="color: var(--warning)"> ~{{ changedCount() }}</span>
          </span>
          <app-copy-button [text]="unifiedText()" label="Copy result" />
        </div>
      </div>

      @if (view() === 'unified') {
        <pre class="input-field h-72 overflow-auto whitespace-pre-wrap font-mono text-xs">{{ unifiedText() }}</pre>
      } @else {
        <div class="input-field h-72 overflow-auto font-mono text-xs">
          @for (row of rows(); track $index) {
            <div class="grid grid-cols-2 gap-2">
              <div [style.background]="rowBg(row.type, 'left')" class="truncate px-1">{{ row.left }}</div>
              <div [style.background]="rowBg(row.type, 'right')" class="truncate px-1">{{ row.right }}</div>
            </div>
          }
        </div>
      }
    </app-dev-tool-shell>
  `,
})
export class DiffToolComponent {
  @Input() toolId = 'diff';
  @Input() title = 'Text Diff / Diff Checker';
  @Input() description = 'Compare two texts side-by-side or as a unified diff.';

  readonly left = signal('');
  readonly right = signal('');
  readonly view = signal<'side' | 'unified'>('side');

  readonly rows = computed(() => computeDiffRows(this.left(), this.right()));
  readonly unifiedText = computed(() => toUnifiedDiff(this.left(), this.right()));

  readonly addedCount = computed(() => this.rows().filter((r) => r.type === 'added').length);
  readonly removedCount = computed(() => this.rows().filter((r) => r.type === 'removed').length);
  readonly changedCount = computed(() => this.rows().filter((r) => r.type === 'changed').length);

  rowBg(type: string, side: 'left' | 'right'): string {
    if (type === 'unchanged') return 'transparent';
    if (type === 'changed') return 'var(--warning-soft)';
    if (type === 'removed' && side === 'left') return 'var(--danger-soft)';
    if (type === 'added' && side === 'right') return 'var(--success-soft)';
    return 'transparent';
  }
}
