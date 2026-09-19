import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';

interface RegexMatch {
  index: number;
  text: string;
  groups: (string | undefined)[];
}

@Component({
  selector: 'app-regex-tester-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent],
  template: `
    <app-dev-tool-shell
      toolId="regex-tester"
      title="Regex Tester"
      description="Test a regular expression against sample text and see matches highlighted."
      icon="regex"
    >
      <div class="flex flex-wrap items-end gap-3 pb-3">
        <div class="min-w-[200px] flex-1">
          <label class="form-label">Pattern</label>
          <div class="flex items-center gap-1 font-mono text-sm">
            <span class="text-[var(--text-muted)]">/</span>
            <input class="input-field" [ngModel]="pattern()" (ngModelChange)="setPattern($event)" placeholder="[a-z]+" />
            <span class="text-[var(--text-muted)]">/{{ flagsString() }}</span>
          </div>
        </div>
        <label class="flex items-center gap-1.5 pb-1.5 text-sm"><input type="checkbox" [ngModel]="g()" (ngModelChange)="setFlag('g', $event)" /> g</label>
        <label class="flex items-center gap-1.5 pb-1.5 text-sm"><input type="checkbox" [ngModel]="i()" (ngModelChange)="setFlag('i', $event)" /> i</label>
        <label class="flex items-center gap-1.5 pb-1.5 text-sm"><input type="checkbox" [ngModel]="m()" (ngModelChange)="setFlag('m', $event)" /> m</label>
        <label class="flex items-center gap-1.5 pb-1.5 text-sm"><input type="checkbox" [ngModel]="s()" (ngModelChange)="setFlag('s', $event)" /> s</label>
      </div>

      <div class="space-y-1 pb-3">
        <label class="form-label">Test text</label>
        <textarea
          class="input-field h-32 resize-y font-mono text-sm"
          [ngModel]="testText()"
          (ngModelChange)="setTestText($event)"
        ></textarea>
      </div>

      @if (error()) {
        <p class="text-sm text-[var(--danger)]">{{ error() }}</p>
      } @else {
        <p class="pb-1 text-sm text-[var(--text-muted)]">{{ matches().length }} match(es)</p>
        <div class="input-field h-32 overflow-auto whitespace-pre-wrap font-mono text-sm">
          @for (seg of segments(); track $index) {
            @if (seg.matched) {
              <mark style="background: var(--primary-soft); color: var(--primary);">{{ seg.text }}</mark>
            } @else {
              {{ seg.text }}
            }
          }
        </div>
        @if (matches().length) {
          <ul class="mt-2 space-y-1 text-xs">
            @for (mtch of matches(); track $index) {
              <li>
                <code>[{{ mtch.index }}]</code> "{{ mtch.text }}"
                @if (mtch.groups.length) {
                  — groups: {{ mtch.groups.join(', ') }}
                }
              </li>
            }
          </ul>
        }
      }
    </app-dev-tool-shell>
  `,
})
export class RegexTesterToolComponent {
  readonly pattern = signal('');
  readonly testText = signal('');
  readonly g = signal(true);
  readonly i = signal(false);
  readonly m = signal(false);
  readonly s = signal(false);
  readonly error = signal<string | null>(null);
  readonly matches = signal<RegexMatch[]>([]);

  readonly flagsString = computed(() => (this.g() ? 'g' : '') + (this.i() ? 'i' : '') + (this.m() ? 'm' : '') + (this.s() ? 's' : ''));

  readonly segments = computed<{ text: string; matched: boolean }[]>(() => {
    const text = this.testText();
    const ms = this.matches();
    if (!ms.length) return [{ text, matched: false }];
    const segs: { text: string; matched: boolean }[] = [];
    let cursor = 0;
    for (const mtch of ms) {
      if (mtch.index > cursor) segs.push({ text: text.slice(cursor, mtch.index), matched: false });
      segs.push({ text: mtch.text, matched: true });
      cursor = mtch.index + mtch.text.length;
    }
    if (cursor < text.length) segs.push({ text: text.slice(cursor), matched: false });
    return segs;
  });

  setPattern(value: string): void {
    this.pattern.set(value);
    this.run();
  }

  setTestText(value: string): void {
    this.testText.set(value);
    this.run();
  }

  setFlag(flag: 'g' | 'i' | 'm' | 's', value: boolean): void {
    ({ g: this.g, i: this.i, m: this.m, s: this.s })[flag].set(value);
    this.run();
  }

  private run(): void {
    if (!this.pattern() || !this.testText()) {
      this.matches.set([]);
      this.error.set(null);
      return;
    }
    try {
      const re = new RegExp(this.pattern(), this.flagsString());
      const results: RegexMatch[] = [];
      if (re.global) {
        let match: RegExpExecArray | null;
        let guard = 0;
        while ((match = re.exec(this.testText())) !== null && guard < 1000) {
          results.push({ index: match.index, text: match[0], groups: match.slice(1) });
          if (match[0] === '') re.lastIndex++;
          guard++;
        }
      } else {
        const match = re.exec(this.testText());
        if (match) results.push({ index: match.index, text: match[0], groups: match.slice(1) });
      }
      this.matches.set(results);
      this.error.set(null);
    } catch (e) {
      this.matches.set([]);
      this.error.set(e instanceof Error ? e.message : String(e));
    }
  }
}
