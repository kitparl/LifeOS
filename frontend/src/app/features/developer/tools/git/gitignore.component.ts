import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';
import { GITIGNORE_PRESETS } from './gitignore-presets.data';

@Component({
  selector: 'app-gitignore-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="gitignore"
      title=".gitignore Generator"
      description="Select common technology stacks and get an editable .gitignore."
      icon="git-branch"
    >
      <div class="flex flex-wrap gap-2 pb-4">
        @for (preset of presets; track preset.id) {
          <label class="flex items-center gap-1.5 rounded-[var(--radius-sm)] border border-[var(--border)] px-2.5 py-1 text-sm">
            <input type="checkbox" [checked]="selected().has(preset.id)" (change)="toggle(preset.id)" />
            {{ preset.label }}
          </label>
        }
      </div>
      <div class="flex justify-end gap-2 pb-2">
        <button type="button" class="btn-ghost" (click)="reset()">Clear</button>
        <app-copy-button [text]="output()" />
      </div>
      <textarea class="input-field h-72 resize-y font-mono text-sm" [ngModel]="output()" (ngModelChange)="edited.set($event)"></textarea>
    </app-dev-tool-shell>
  `,
})
export class GitignoreToolComponent {
  readonly presets = GITIGNORE_PRESETS;
  readonly selected = signal<Set<string>>(new Set());
  readonly edited = signal<string | null>(null);

  readonly generated = computed(() => {
    const blocks: string[] = [];
    for (const preset of this.presets) {
      if (this.selected().has(preset.id)) {
        blocks.push(`# ${preset.label}\n${preset.content}`);
      }
    }
    return blocks.join('\n\n');
  });

  readonly output = computed(() => this.edited() ?? this.generated());

  toggle(id: string): void {
    const next = new Set(this.selected());
    if (next.has(id)) next.delete(id);
    else next.add(id);
    this.selected.set(next);
    this.edited.set(null);
  }

  reset(): void {
    this.selected.set(new Set());
    this.edited.set(null);
  }
}
