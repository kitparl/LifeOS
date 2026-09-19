import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';

@Component({
  selector: 'app-text-counter-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent],
  template: `
    <app-dev-tool-shell
      toolId="text-counter"
      title="Line / Word / Character Counter"
      description="Count lines, words, and characters in text."
      icon="list-ordered"
    >
      <div class="grid grid-cols-2 gap-3 pb-4 sm:grid-cols-4">
        <div class="panel panel--flat text-center">
          <p class="text-2xl font-semibold">{{ stats().lines }}</p>
          <p class="text-xs text-[var(--text-muted)]">Lines</p>
        </div>
        <div class="panel panel--flat text-center">
          <p class="text-2xl font-semibold">{{ stats().words }}</p>
          <p class="text-xs text-[var(--text-muted)]">Words</p>
        </div>
        <div class="panel panel--flat text-center">
          <p class="text-2xl font-semibold">{{ stats().characters }}</p>
          <p class="text-xs text-[var(--text-muted)]">Characters</p>
        </div>
        <div class="panel panel--flat text-center">
          <p class="text-2xl font-semibold">{{ stats().charactersNoSpaces }}</p>
          <p class="text-xs text-[var(--text-muted)]">Characters (no spaces)</p>
        </div>
      </div>
      <textarea
        class="input-field h-56 resize-y text-sm"
        placeholder="Type or paste text…"
        [ngModel]="text()"
        (ngModelChange)="text.set($event)"
      ></textarea>
    </app-dev-tool-shell>
  `,
})
export class TextCounterToolComponent {
  readonly text = signal('');

  readonly stats = computed(() => {
    const t = this.text();
    return {
      lines: t ? t.split('\n').length : 0,
      words: t.trim() ? t.trim().split(/\s+/).length : 0,
      characters: t.length,
      charactersNoSpaces: t.replace(/\s/g, '').length,
    };
  });
}
