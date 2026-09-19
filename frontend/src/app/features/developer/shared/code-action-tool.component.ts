import { Component, Input, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from './dev-tool-shell.component';
import { CopyButtonComponent } from './copy-button.component';
import { DevHistoryPanelComponent } from './dev-history-panel.component';
import { DevHistoryService } from './dev-history.service';

const HISTORY_DEBOUNCE_MS = 900;

/** Generic Format/Minify tool for a bracket-based language. Shared by HTML/CSS/JS/SQL Formatters. */
@Component({
  selector: 'app-code-action-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent, DevHistoryPanelComponent],
  template: `
    <app-dev-tool-shell [title]="title" [description]="description" [icon]="icon" [toolId]="toolId">
      <div class="flex flex-wrap items-center justify-between gap-2 pb-3">
        <div class="inline-flex overflow-hidden rounded-[var(--radius-sm)] border border-[var(--border)]">
          <button
            type="button"
            class="px-3 py-1.5 text-sm"
            [style.background]="mode() === 'format' ? 'var(--primary)' : 'transparent'"
            [style.color]="mode() === 'format' ? '#fff' : 'var(--text)'"
            (click)="setMode('format')"
          >
            Format
          </button>
          <button
            type="button"
            class="px-3 py-1.5 text-sm border-l border-[var(--border)]"
            [style.background]="mode() === 'minify' ? 'var(--primary)' : 'transparent'"
            [style.color]="mode() === 'minify' ? '#fff' : 'var(--text)'"
            (click)="setMode('minify')"
          >
            Minify
          </button>
        </div>
        <div class="flex items-center gap-2">
          <button type="button" class="btn-ghost" (click)="clear()">Clear</button>
          <app-copy-button [text]="output()" />
        </div>
      </div>

      <div class="grid gap-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">Input</label>
          <textarea
            class="input-field h-64 resize-y font-mono text-sm"
            [placeholder]="placeholder"
            [ngModel]="input()"
            (ngModelChange)="onInputChange($event)"
          ></textarea>
        </div>
        <div class="space-y-1">
          <label class="form-label">Output</label>
          <textarea class="input-field h-64 resize-y font-mono text-sm" readonly [ngModel]="output()"></textarea>
          @if (error()) {
            <p class="text-xs text-[var(--danger)]">{{ error() }}</p>
          }
        </div>
      </div>

      <app-dev-history-panel [toolId]="toolId" />
    </app-dev-tool-shell>
  `,
})
export class CodeActionToolComponent implements OnInit, OnDestroy {
  @Input({ required: true }) title = '';
  @Input({ required: true }) description = '';
  @Input() icon = 'code';
  @Input({ required: true }) toolId = '';
  @Input({ required: true }) formatFn!: (input: string) => string;
  @Input({ required: true }) minifyFn!: (input: string) => string;
  @Input() placeholder = 'Paste code…';

  private readonly historyService = inject(DevHistoryService);
  private historyTimer: ReturnType<typeof setTimeout> | undefined;

  readonly mode = signal<'format' | 'minify'>('format');
  readonly input = signal('');
  readonly output = signal('');
  readonly error = signal<string | null>(null);

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

  setMode(mode: 'format' | 'minify'): void {
    this.mode.set(mode);
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
      return;
    }
    try {
      this.output.set(this.mode() === 'format' ? this.formatFn(text) : this.minifyFn(text));
      this.error.set(null);
      this.scheduleHistoryRecord(text, this.output());
    } catch (e) {
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
