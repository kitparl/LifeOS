import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';

const COMMIT_TYPES = ['feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'build', 'ci', 'chore', 'revert'];

@Component({
  selector: 'app-commit-message-generator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="commit-message-generator"
      title="Conventional Git Commit Message Generator"
      description="Build a Conventional Commits message."
      icon="git-commit"
    >
      <div class="grid gap-3 pb-3 sm:grid-cols-3">
        <div>
          <label class="form-label">Type</label>
          <select class="input-field" [ngModel]="type()" (ngModelChange)="type.set($event)">
            @for (t of types; track t) {
              <option [value]="t">{{ t }}</option>
            }
          </select>
        </div>
        <div>
          <label class="form-label">Scope (optional)</label>
          <input class="input-field" [ngModel]="scope()" (ngModelChange)="scope.set($event)" placeholder="api" />
        </div>
        <label class="flex items-end gap-1.5 pb-2 text-sm">
          <input type="checkbox" [ngModel]="breaking()" (ngModelChange)="breaking.set($event)" /> Breaking change
        </label>
      </div>
      <div class="space-y-1 pb-3">
        <label class="form-label">Short description</label>
        <input class="input-field" [ngModel]="description()" (ngModelChange)="description.set($event)" placeholder="add pagination to results list" />
      </div>
      <div class="space-y-1 pb-3">
        <label class="form-label">Body (optional)</label>
        <textarea class="input-field h-24 resize-y" [ngModel]="body()" (ngModelChange)="body.set($event)"></textarea>
      </div>
      <div class="space-y-1 pb-3">
        <label class="form-label">Footer (optional — e.g. "Closes #123")</label>
        <input class="input-field" [ngModel]="footer()" (ngModelChange)="footer.set($event)" />
      </div>
      <div class="flex items-start gap-2">
        <pre class="input-field flex-1 whitespace-pre-wrap font-mono text-sm">{{ message() }}</pre>
        <app-copy-button [text]="message()" />
      </div>
    </app-dev-tool-shell>
  `,
})
export class CommitMessageGeneratorToolComponent {
  readonly types = COMMIT_TYPES;
  readonly type = signal('feat');
  readonly scope = signal('');
  readonly breaking = signal(false);
  readonly description = signal('');
  readonly body = signal('');
  readonly footer = signal('');

  readonly message = computed(() => {
    const scopePart = this.scope().trim() ? `(${this.scope().trim()})` : '';
    const bang = this.breaking() ? '!' : '';
    const header = `${this.type()}${scopePart}${bang}: ${this.description().trim() || '<description>'}`;
    const parts = [header];
    if (this.body().trim()) parts.push(this.body().trim());
    const footers: string[] = [];
    if (this.breaking()) footers.push(`BREAKING CHANGE: ${this.description().trim() || 'describe the breaking change'}`);
    if (this.footer().trim()) footers.push(this.footer().trim());
    if (footers.length) parts.push(footers.join('\n'));
    return parts.join('\n\n');
  });
}
