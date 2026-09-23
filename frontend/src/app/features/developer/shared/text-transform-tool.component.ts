import { Component, ElementRef, Input, OnDestroy, OnInit, ViewChild, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from './dev-tool-shell.component';
import { CopyButtonComponent } from './copy-button.component';
import { DevHistoryPanelComponent } from './dev-history-panel.component';
import { DevHistoryEntry, DevHistoryService } from './dev-history.service';

export type TransformDirection = 'forward' | 'backward';

const HISTORY_DEBOUNCE_MS = 900;

/**
 * Generic bidirectional text-transform engine. Reused by every Encoding & Decoding tool
 * that is a pure, reversible pair (Base64, URL, HTML entities, Hex, Binary, ASCII, Unicode,
 * Base32, Base58) so each route component is a thin wrapper supplying only the two functions.
 */
@Component({
  selector: 'app-text-transform-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent, DevHistoryPanelComponent],
  template: `
    <app-dev-tool-shell [title]="title" [description]="description" [icon]="icon" [toolId]="toolId">
      <div class="flex flex-wrap items-center justify-between gap-2 pb-3">
        <div class="inline-flex overflow-hidden rounded-[var(--radius-sm)] border border-[var(--border)]">
          <button
            type="button"
            class="px-3 py-1.5 text-sm"
            [style.background]="mode() === 'forward' ? 'var(--primary)' : 'transparent'"
            [style.color]="mode() === 'forward' ? '#fff' : 'var(--text)'"
            (click)="setMode('forward')"
          >
            {{ forwardLabel }}
          </button>
          <button
            type="button"
            class="px-3 py-1.5 text-sm border-l border-[var(--border)]"
            [style.background]="mode() === 'backward' ? 'var(--primary)' : 'transparent'"
            [style.color]="mode() === 'backward' ? '#fff' : 'var(--text)'"
            (click)="setMode('backward')"
          >
            {{ backwardLabel }}
          </button>
        </div>
        <div class="flex items-center gap-2">
          @if (isOutputJson()) {
            <label class="flex items-center gap-1.5 text-sm">
              <input type="checkbox" [ngModel]="prettyJson()" (ngModelChange)="prettyJson.set($event)" />
              Pretty-print JSON
            </label>
          }
          <button type="button" class="btn-secondary" (click)="swap()">Swap</button>
          <button type="button" class="btn-ghost" (click)="clear()">Clear</button>
          <app-copy-button [text]="displayOutput()" />
        </div>
      </div>

      <div class="grid gap-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">{{ mode() === 'forward' ? 'Input' : backwardLabel + ' input' }}</label>
          <textarea
            #mainInput
            class="input-field h-56 resize-y font-mono text-sm"
            [placeholder]="placeholder"
            [ngModel]="input()"
            (ngModelChange)="onInputChange($event)"
          ></textarea>
          <p class="text-xs text-[var(--text-muted)]">{{ charCount() }} chars · {{ byteCount() }} bytes</p>
        </div>
        <div class="space-y-1">
          <label class="form-label">Output</label>
          <textarea
            class="input-field h-56 resize-y font-mono text-sm"
            readonly
            [ngModel]="displayOutput()"
          ></textarea>
          @if (error()) {
            <p class="text-xs text-[var(--danger)]">{{ error() }}</p>
          } @else {
            <p class="text-xs text-[var(--text-muted)]">{{ output().length }} chars</p>
          }
        </div>
      </div>

      <app-dev-history-panel [toolId]="toolId" (reuse)="onReuse($event)" />
    </app-dev-tool-shell>
  `,
})
export class TextTransformToolComponent implements OnInit, OnDestroy {
  @Input({ required: true }) title = '';
  @Input({ required: true }) description = '';
  @Input() icon = '';
  @Input({ required: true }) toolId = '';
  @Input() forwardLabel = 'Encode';
  @Input() backwardLabel = 'Decode';
  @Input({ required: true }) encodeFn!: (value: string) => string;
  @Input({ required: true }) decodeFn!: (value: string) => string;
  @Input() placeholder = 'Type or paste text…';
  /** When true, offers a "Pretty-print JSON" toggle if the decoded output happens to be valid JSON (used by Base64). */
  @Input() detectJson = false;

  @ViewChild('mainInput') private readonly mainInput?: ElementRef<HTMLTextAreaElement>;

  private readonly historyService = inject(DevHistoryService);
  private historyTimer: ReturnType<typeof setTimeout> | undefined;

  readonly mode = signal<TransformDirection>('forward');
  readonly input = signal('');
  readonly output = signal('');
  readonly error = signal<string | null>(null);
  readonly prettyJson = signal(false);

  readonly isOutputJson = computed(() => {
    if (!this.detectJson || this.mode() !== 'backward' || !this.output()) return false;
    try {
      JSON.parse(this.output());
      return true;
    } catch {
      return false;
    }
  });

  readonly displayOutput = computed(() => {
    if (this.isOutputJson() && this.prettyJson()) {
      try {
        return JSON.stringify(JSON.parse(this.output()), null, 2);
      } catch {
        return this.output();
      }
    }
    return this.output();
  });

  ngOnInit(): void {
    this.recompute();
  }

  ngOnDestroy(): void {
    clearTimeout(this.historyTimer);
  }

  onInputChange(value: string): void {
    this.input.set(value);
    this.recompute();
  }

  onReuse(entry: DevHistoryEntry): void {
    this.onInputChange(entry.input);
    this.mainInput?.nativeElement.focus();
    this.mainInput?.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  setMode(mode: TransformDirection): void {
    this.mode.set(mode);
    this.recompute();
  }

  swap(): void {
    const previousOutput = this.output();
    this.mode.set(this.mode() === 'forward' ? 'backward' : 'forward');
    if (!this.error()) {
      this.input.set(previousOutput);
    }
    this.recompute();
  }

  clear(): void {
    this.input.set('');
    this.recompute();
  }

  charCount(): number {
    return this.input().length;
  }

  byteCount(): number {
    return new TextEncoder().encode(this.input()).length;
  }

  private recompute(): void {
    const text = this.input();
    if (!text) {
      this.output.set('');
      this.error.set(null);
      return;
    }
    try {
      const fn = this.mode() === 'forward' ? this.encodeFn : this.decodeFn;
      const result = fn(text);
      this.output.set(result);
      this.error.set(null);
      this.scheduleHistoryRecord(text, result);
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
