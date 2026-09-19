import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { reindentCode } from '../../shared/brace-formatter.util';

const LANGUAGES = ['JavaScript', 'TypeScript', 'Java', 'C', 'C++', 'C#', 'Go', 'Rust', 'PHP', 'JSON', 'CSS'];

@Component({
  selector: 'app-code-beautifier-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="code-beautifier"
      title="Code Beautifier"
      description="Re-indent code in a bracket-based language by nesting depth. A lightweight beautifier — it doesn't reflow lines or apply language-specific style rules."
      icon="wand"
    >
      <div class="flex flex-wrap items-end justify-between gap-3 pb-3">
        <div>
          <label class="form-label">Language</label>
          <select class="input-field w-auto" [ngModel]="language()" (ngModelChange)="language.set($event)">
            @for (lang of languages; track lang) {
              <option [value]="lang">{{ lang }}</option>
            }
          </select>
        </div>
        <div class="flex items-center gap-2">
          <button type="button" class="btn-ghost" (click)="clear()">Clear</button>
          <app-copy-button [text]="output()" />
        </div>
      </div>
      <div class="grid gap-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">Input</label>
          <textarea class="input-field h-64 resize-y font-mono text-sm" [ngModel]="input()" (ngModelChange)="onInputChange($event)"></textarea>
        </div>
        <div class="space-y-1">
          <label class="form-label">Output</label>
          <textarea class="input-field h-64 resize-y font-mono text-sm" readonly [ngModel]="output()"></textarea>
        </div>
      </div>
    </app-dev-tool-shell>
  `,
})
export class CodeBeautifierToolComponent implements OnInit {
  readonly languages = LANGUAGES;
  readonly language = signal('JavaScript');
  readonly input = signal('');
  readonly output = signal('');

  ngOnInit(): void {
    this.run();
  }

  onInputChange(value: string): void {
    this.input.set(value);
    this.run();
  }

  clear(): void {
    this.input.set('');
    this.run();
  }

  private run(): void {
    this.output.set(this.input().trim() ? reindentCode(this.input()) : '');
  }
}
