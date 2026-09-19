import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';

interface ParamRow {
  key: string;
  value: string;
}

@Component({
  selector: 'app-querystring-parser-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="querystring-parser"
      title="Query String Parser / Builder"
      description="Parse a query string into key/value pairs, or build one from rows."
      icon="link"
    >
      <div class="flex justify-end pb-3">
        <div class="inline-flex overflow-hidden rounded-[var(--radius-sm)] border border-[var(--border)]">
          <button type="button" class="px-3 py-1.5 text-sm" [style.background]="mode() === 'parse' ? 'var(--primary)' : 'transparent'" [style.color]="mode() === 'parse' ? '#fff' : 'var(--text)'" (click)="mode.set('parse')">Parse</button>
          <button type="button" class="px-3 py-1.5 text-sm border-l border-[var(--border)]" [style.background]="mode() === 'build' ? 'var(--primary)' : 'transparent'" [style.color]="mode() === 'build' ? '#fff' : 'var(--text)'" (click)="mode.set('build')">Build</button>
        </div>
      </div>

      @if (mode() === 'parse') {
        <div class="space-y-1 pb-3">
          <label class="form-label">Query string or URL</label>
          <input class="input-field font-mono text-sm" placeholder="?a=1&b=2" [ngModel]="parseInput()" (ngModelChange)="parseInput.set($event)" />
        </div>
        @if (parsedRows().length) {
          <ul class="space-y-1 text-sm">
            @for (row of parsedRows(); track row.key + row.value) {
              <li><code>{{ row.key }}</code> = {{ row.value }}</li>
            }
          </ul>
        } @else {
          <p class="text-sm text-[var(--text-muted)]">Enter a query string above.</p>
        }
      } @else {
        <div class="space-y-2 pb-3">
          @for (row of buildRows(); track $index) {
            <div class="flex gap-2">
              <input class="input-field font-mono text-sm" placeholder="key" [ngModel]="row.key" (ngModelChange)="setBuildKey($index, $event)" />
              <input class="input-field font-mono text-sm" placeholder="value" [ngModel]="row.value" (ngModelChange)="setBuildValue($index, $event)" />
              <button type="button" class="btn-ghost" (click)="removeRow($index)">Remove</button>
            </div>
          }
          <button type="button" class="btn-secondary" (click)="addRow()">Add param</button>
        </div>
        <div class="flex items-center gap-2">
          <input class="input-field font-mono text-sm" readonly [ngModel]="builtQuery()" />
          <app-copy-button [text]="builtQuery()" />
        </div>
      }
    </app-dev-tool-shell>
  `,
})
export class QuerystringParserToolComponent {
  readonly mode = signal<'parse' | 'build'>('parse');
  readonly parseInput = signal('');
  readonly buildRows = signal<ParamRow[]>([{ key: '', value: '' }]);

  readonly parsedRows = computed<ParamRow[]>(() => {
    const raw = this.parseInput().trim();
    if (!raw) return [];
    const queryPart = raw.includes('?') ? raw.slice(raw.indexOf('?') + 1) : raw.replace(/^\?/, '');
    const params = new URLSearchParams(queryPart);
    return Array.from(params.entries()).map(([key, value]) => ({ key, value }));
  });

  readonly builtQuery = computed(() => {
    const params = new URLSearchParams();
    for (const row of this.buildRows()) {
      if (row.key) params.append(row.key, row.value);
    }
    const s = params.toString();
    return s ? `?${s}` : '';
  });

  setBuildKey(index: number, value: string): void {
    const rows = [...this.buildRows()];
    rows[index] = { ...rows[index], key: value };
    this.buildRows.set(rows);
  }

  setBuildValue(index: number, value: string): void {
    const rows = [...this.buildRows()];
    rows[index] = { ...rows[index], value };
    this.buildRows.set(rows);
  }

  addRow(): void {
    this.buildRows.set([...this.buildRows(), { key: '', value: '' }]);
  }

  removeRow(index: number): void {
    const rows = this.buildRows().filter((_, i) => i !== index);
    this.buildRows.set(rows.length ? rows : [{ key: '', value: '' }]);
  }
}
