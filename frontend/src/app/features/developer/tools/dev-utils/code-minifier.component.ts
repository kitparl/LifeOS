import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { minifyCode } from '../../shared/brace-formatter.util';
import { minifyCss } from '../web/css.util';

@Component({
  selector: 'app-code-minifier-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="code-minifier"
      title="Code Minifier"
      description="Minify JavaScript or CSS by stripping comments and collapsing whitespace."
      icon="wand"
    >
      <div class="flex flex-wrap items-end justify-between gap-3 pb-3">
        <div class="inline-flex overflow-hidden rounded-[var(--radius-sm)] border border-[var(--border)]">
          <button type="button" class="px-3 py-1.5 text-sm" [style.background]="language() === 'js' ? 'var(--primary)' : 'transparent'" [style.color]="language() === 'js' ? '#fff' : 'var(--text)'" (click)="setLanguage('js')">JavaScript</button>
          <button type="button" class="px-3 py-1.5 text-sm border-l border-[var(--border)]" [style.background]="language() === 'css' ? 'var(--primary)' : 'transparent'" [style.color]="language() === 'css' ? '#fff' : 'var(--text)'" (click)="setLanguage('css')">CSS</button>
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
export class CodeMinifierToolComponent implements OnInit {
  readonly language = signal<'js' | 'css'>('js');
  readonly input = signal('');
  readonly output = signal('');

  ngOnInit(): void {
    this.run();
  }

  setLanguage(lang: 'js' | 'css'): void {
    this.language.set(lang);
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
    if (!this.input().trim()) {
      this.output.set('');
      return;
    }
    this.output.set(this.language() === 'js' ? minifyCode(this.input()) : minifyCss(this.input()));
  }
}
