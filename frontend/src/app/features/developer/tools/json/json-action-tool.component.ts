import { Component, ElementRef, Input, OnDestroy, OnInit, ViewChild, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { DevHistoryPanelComponent } from '../../shared/dev-history-panel.component';
import { DevHistoryEntry, DevHistoryService } from '../../shared/dev-history.service';
import { parseJsonOrThrow } from './json.util';

export type JsonAction = 'format' | 'validate' | 'minify';

const HISTORY_DEBOUNCE_MS = 900;

/** Generic single-direction JSON tool: shared by JSON Formatter, JSON Validator, and JSON Minifier. */
@Component({
  selector: 'app-json-action-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent, DevHistoryPanelComponent],
  template: `
    <app-dev-tool-shell [title]="title" [description]="description" [icon]="icon" [toolId]="toolId">
      <div class="flex flex-wrap items-center justify-between gap-2 pb-3">
        @if (mode === 'format') {
          <div class="flex items-center gap-2 text-sm">
            <label class="text-[var(--text-muted)]">Indent</label>
            <select class="input-field w-auto" [ngModel]="indent()" (ngModelChange)="setIndent(+$event)">
              <option [ngValue]="2">2 spaces</option>
              <option [ngValue]="4">4 spaces</option>
              <option [ngValue]="0">Tab</option>
            </select>
          </div>
        } @else {
          <span></span>
        }
        <div class="flex items-center gap-2">
          <button type="button" class="btn-ghost" (click)="clear()">Clear</button>
          <app-copy-button [text]="output()" />
        </div>
      </div>

      <div class="grid gap-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">JSON input</label>
          <textarea
            #mainInput
            class="input-field h-64 resize-y font-mono text-sm"
            placeholder="Paste JSON…"
            [ngModel]="input()"
            (ngModelChange)="onInputChange($event)"
          ></textarea>
        </div>
        <div class="space-y-1">
          <label class="form-label">
            {{ mode === 'validate' ? 'Result' : 'Output' }}
            @if (valid() === true) {
              <span class="badge" style="background: var(--success-soft); color: var(--success);">Valid</span>
            } @else if (valid() === false) {
              <span class="badge" style="background: var(--danger-soft); color: var(--danger);">Invalid</span>
            }
          </label>
          <textarea class="input-field h-64 resize-y font-mono text-sm" readonly [ngModel]="output()"></textarea>
          @if (error()) {
            <p class="text-xs text-[var(--danger)]">{{ error() }}</p>
          }
        </div>
      </div>

      <app-dev-history-panel [toolId]="toolId" (reuse)="onReuse($event)" />
    </app-dev-tool-shell>
  `,
})
export class JsonActionToolComponent implements OnInit, OnDestroy {
  @Input({ required: true }) title = '';
  @Input({ required: true }) description = '';
  @Input() icon = 'braces';
  @Input({ required: true }) toolId = '';
  @Input({ required: true }) mode: JsonAction = 'format';

  @ViewChild('mainInput') private readonly mainInput?: ElementRef<HTMLTextAreaElement>;

  private readonly historyService = inject(DevHistoryService);
  private historyTimer: ReturnType<typeof setTimeout> | undefined;

  readonly input = signal('');
  readonly output = signal('');
  readonly error = signal<string | null>(null);
  readonly valid = signal<boolean | null>(null);
  readonly indent = signal(2);

  ngOnInit(): void {
    this.run();
  }

  ngOnDestroy(): void {
    clearTimeout(this.historyTimer);
  }

  onInputChange(value: string): void {
    this.input.set(value);
    this.run();
  }

  onReuse(entry: DevHistoryEntry): void {
    this.onInputChange(entry.input);
    this.mainInput?.nativeElement.focus();
    this.mainInput?.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  setIndent(value: number): void {
    this.indent.set(value);
    this.run();
  }

  clear(): void {
    this.input.set('');
    this.run();
  }

  private run(): void {
    const text = this.input();
    if (!text.trim()) {
      this.output.set('');
      this.error.set(null);
      this.valid.set(null);
      return;
    }
    try {
      const parsed = parseJsonOrThrow(text);
      this.valid.set(true);
      this.error.set(null);
      if (this.mode === 'format') {
        this.output.set(JSON.stringify(parsed, null, this.indent() === 0 ? '\t' : this.indent()));
      } else if (this.mode === 'minify') {
        this.output.set(JSON.stringify(parsed));
      } else {
        this.output.set('Valid JSON.');
      }
      this.scheduleHistoryRecord(text, this.output());
    } catch (e) {
      this.valid.set(false);
      this.output.set('');
      this.error.set(e instanceof Error ? e.message : String(e));
    }
  }

  private scheduleHistoryRecord(input: string, output: string): void {
    clearTimeout(this.historyTimer);
    this.historyTimer = setTimeout(() => {
      void this.historyService.addEntry(this.toolId, input, output);
    }, HISTORY_DEBOUNCE_MS);
  }
}
