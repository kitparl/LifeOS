import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { uuidV4, uuidV7 } from './generators.util';

@Component({
  selector: 'app-uuid-generator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="uuid-generator"
      title="UUID Generator"
      description="Generate UUID v4 (random) or v7 (time-ordered) identifiers, using the browser's secure randomness."
      icon="fingerprint"
    >
      <div class="flex flex-wrap items-end justify-between gap-3 pb-3">
        <div class="flex items-end gap-3">
          <div class="inline-flex overflow-hidden rounded-[var(--radius-sm)] border border-[var(--border)]">
            <button type="button" class="px-3 py-1.5 text-sm" [style.background]="version() === 'v4' ? 'var(--primary)' : 'transparent'" [style.color]="version() === 'v4' ? '#fff' : 'var(--text)'" (click)="setVersion('v4')">v4</button>
            <button type="button" class="px-3 py-1.5 text-sm border-l border-[var(--border)]" [style.background]="version() === 'v7' ? 'var(--primary)' : 'transparent'" [style.color]="version() === 'v7' ? '#fff' : 'var(--text)'" (click)="setVersion('v7')">v7</button>
          </div>
          <div>
            <label class="form-label">Count</label>
            <input class="input-field w-24" type="number" min="1" max="100" [ngModel]="count()" (ngModelChange)="setCount(+$event)" />
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button type="button" class="btn-primary" (click)="regenerate()">Generate</button>
          <app-copy-button [text]="output()" />
        </div>
      </div>
      <textarea class="input-field h-56 resize-y font-mono text-sm" readonly [ngModel]="output()"></textarea>
    </app-dev-tool-shell>
  `,
})
export class UuidGeneratorToolComponent implements OnInit {
  readonly version = signal<'v4' | 'v7'>('v4');
  readonly count = signal(5);
  readonly output = signal('');

  ngOnInit(): void {
    this.regenerate();
  }

  setVersion(v: 'v4' | 'v7'): void {
    this.version.set(v);
    this.regenerate();
  }

  setCount(v: number): void {
    this.count.set(Math.min(100, Math.max(1, v || 1)));
  }

  regenerate(): void {
    const gen = this.version() === 'v4' ? uuidV4 : uuidV7;
    this.output.set(Array.from({ length: this.count() }, () => gen()).join('\n'));
  }
}
