import { Component, Input, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from './dev-tool-shell.component';
import { CopyButtonComponent } from './copy-button.component';
import { DevHistoryPanelComponent } from './dev-history-panel.component';
import { DevHistoryService } from './dev-history.service';
import { parseJsonOrThrow } from '../tools/json/json.util';
import { CodeGenOptions } from './json-codegen.util';

const HISTORY_DEBOUNCE_MS = 900;

/** Generic JSON -> typed-model tool. Shared by all 6 JSON -> language routes. */
@Component({
  selector: 'app-json-codegen-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent, DevHistoryPanelComponent],
  template: `
    <app-dev-tool-shell [title]="title" [description]="description" [icon]="icon" [toolId]="toolId">
      <div class="flex flex-wrap items-end justify-between gap-3 pb-3">
        <div class="flex flex-wrap items-end gap-3">
          <div>
            <label class="form-label">Root type name</label>
            <input class="input-field w-40" [ngModel]="rootName()" (ngModelChange)="setRootName($event)" />
          </div>
          <label class="flex items-center gap-1.5 pb-1.5 text-sm">
            <input type="checkbox" [ngModel]="optionalFields()" (ngModelChange)="setOptionalFields($event)" />
            Optional fields
          </label>
          <label class="flex items-center gap-1.5 pb-1.5 text-sm">
            <input type="checkbox" [ngModel]="nullableFields()" (ngModelChange)="setNullableFields($event)" />
            Nullable fields
          </label>
          @if (showUseType) {
            <label class="flex items-center gap-1.5 pb-1.5 text-sm">
              <input type="checkbox" [ngModel]="useType()" (ngModelChange)="setUseType($event)" />
              Use "type" instead of "interface"
            </label>
          }
        </div>
        <div class="flex items-center gap-2">
          <button type="button" class="btn-ghost" (click)="clear()">Clear</button>
          <app-copy-button [text]="output()" />
        </div>
      </div>

      <div class="grid gap-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">JSON input</label>
          <textarea
            class="input-field h-64 resize-y font-mono text-sm"
            placeholder="Paste a JSON object or array…"
            [ngModel]="input()"
            (ngModelChange)="onInputChange($event)"
          ></textarea>
        </div>
        <div class="space-y-1">
          <label class="form-label">Generated code</label>
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
export class JsonCodeGenToolComponent implements OnInit, OnDestroy {
  @Input({ required: true }) title = '';
  @Input({ required: true }) description = '';
  @Input() icon = 'file-code-2';
  @Input({ required: true }) toolId = '';
  @Input({ required: true }) generateFn!: (rootName: string, value: unknown, opts: CodeGenOptions) => string;
  @Input() showUseType = false;
  @Input() defaultRootName = 'Root';
  @Input() defaultNullableFields = true;

  private readonly historyService = inject(DevHistoryService);
  private historyTimer: ReturnType<typeof setTimeout> | undefined;

  readonly input = signal('');
  readonly output = signal('');
  readonly error = signal<string | null>(null);
  readonly rootName = signal('Root');
  readonly optionalFields = signal(false);
  readonly nullableFields = signal(true);
  readonly useType = signal(false);

  ngOnInit(): void {
    this.rootName.set(this.defaultRootName);
    this.nullableFields.set(this.defaultNullableFields);
    this.run();
  }

  ngOnDestroy(): void {
    clearTimeout(this.historyTimer);
  }

  onInputChange(value: string): void {
    this.input.set(value);
    this.run();
  }

  setRootName(value: string): void {
    this.rootName.set(value || 'Root');
    this.run();
  }

  setOptionalFields(value: boolean): void {
    this.optionalFields.set(value);
    this.run();
  }

  setNullableFields(value: boolean): void {
    this.nullableFields.set(value);
    this.run();
  }

  setUseType(value: boolean): void {
    this.useType.set(value);
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
      const value = parseJsonOrThrow(text);
      this.output.set(
        this.generateFn(this.rootName(), value, {
          optionalFields: this.optionalFields(),
          nullableFields: this.nullableFields(),
          useType: this.useType(),
        }),
      );
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
