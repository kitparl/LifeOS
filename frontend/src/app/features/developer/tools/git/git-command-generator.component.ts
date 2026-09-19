import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';

type GitOp = 'clone' | 'branch' | 'checkout' | 'switch' | 'add' | 'commit' | 'push' | 'pull' | 'merge' | 'rebase' | 'stash' | 'reset' | 'revert' | 'tag' | 'remote';

const OPERATIONS: { id: GitOp; label: string; placeholder: string }[] = [
  { id: 'clone', label: 'clone', placeholder: 'repository URL' },
  { id: 'branch', label: 'branch', placeholder: 'branch name (optional — lists branches if empty)' },
  { id: 'checkout', label: 'checkout', placeholder: 'branch or commit' },
  { id: 'switch', label: 'switch', placeholder: 'branch name' },
  { id: 'add', label: 'add', placeholder: 'files (default: .)' },
  { id: 'commit', label: 'commit', placeholder: 'commit message' },
  { id: 'push', label: 'push', placeholder: 'branch name' },
  { id: 'pull', label: 'pull', placeholder: 'branch name' },
  { id: 'merge', label: 'merge', placeholder: 'branch to merge in' },
  { id: 'rebase', label: 'rebase', placeholder: 'branch or commit' },
  { id: 'stash', label: 'stash', placeholder: 'stash message (optional)' },
  { id: 'reset', label: 'reset', placeholder: 'target (default: HEAD~1)' },
  { id: 'revert', label: 'revert', placeholder: 'commit to revert' },
  { id: 'tag', label: 'tag', placeholder: 'tag name' },
  { id: 'remote', label: 'remote add', placeholder: 'remote URL' },
];

@Component({
  selector: 'app-git-command-generator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="git-command-generator"
      title="Git Command Generator"
      description="Build common git commands from a simple form."
      icon="git-branch"
    >
      <div class="grid gap-3 pb-3 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <label class="form-label">Operation</label>
          <select class="input-field" [ngModel]="operation()" (ngModelChange)="operation.set($event)">
            @for (op of operations; track op.id) {
              <option [value]="op.id">{{ op.label }}</option>
            }
          </select>
        </div>
        <div class="sm:col-span-1 lg:col-span-2">
          <label class="form-label">{{ currentPlaceholder() }}</label>
          <input class="input-field font-mono text-sm" [ngModel]="primaryValue()" (ngModelChange)="primaryValue.set($event)" />
        </div>
        <div>
          <label class="form-label">Remote name</label>
          <input class="input-field font-mono text-sm" [ngModel]="remoteName()" (ngModelChange)="remoteName.set($event)" placeholder="origin" />
        </div>
      </div>
      <div class="space-y-1 pb-3">
        <label class="form-label">Extra flags (optional, appended verbatim)</label>
        <input class="input-field font-mono text-sm" [ngModel]="extraFlags()" (ngModelChange)="extraFlags.set($event)" placeholder="--force" />
      </div>
      <div class="flex items-center gap-2">
        <input class="input-field font-mono text-sm" readonly [ngModel]="command()" />
        <app-copy-button [text]="command()" />
      </div>
    </app-dev-tool-shell>
  `,
})
export class GitCommandGeneratorToolComponent {
  readonly operations = OPERATIONS;
  readonly operation = signal<GitOp>('commit');
  readonly primaryValue = signal('');
  readonly remoteName = signal('origin');
  readonly extraFlags = signal('');

  readonly currentPlaceholder = computed(() => this.operations.find((o) => o.id === this.operation())?.placeholder ?? '');

  readonly command = computed(() => {
    const v = this.primaryValue().trim();
    const remote = this.remoteName().trim() || 'origin';
    const flags = this.extraFlags().trim();
    const withFlags = (cmd: string): string => (flags ? `${cmd} ${flags}` : cmd);
    switch (this.operation()) {
      case 'clone':
        return withFlags(`git clone ${v || '<repository-url>'}`);
      case 'branch':
        return withFlags(v ? `git branch ${v}` : 'git branch');
      case 'checkout':
        return withFlags(`git checkout ${v || '<branch>'}`);
      case 'switch':
        return withFlags(`git switch ${v || '<branch>'}`);
      case 'add':
        return withFlags(`git add ${v || '.'}`);
      case 'commit':
        return withFlags(`git commit -m "${v || '<message>'}"`);
      case 'push':
        return withFlags(`git push ${remote} ${v || '<branch>'}`);
      case 'pull':
        return withFlags(`git pull ${remote} ${v || '<branch>'}`);
      case 'merge':
        return withFlags(`git merge ${v || '<branch>'}`);
      case 'rebase':
        return withFlags(`git rebase ${v || '<branch>'}`);
      case 'stash':
        return withFlags(v ? `git stash push -m "${v}"` : 'git stash');
      case 'reset':
        return withFlags(`git reset --mixed ${v || 'HEAD~1'}`);
      case 'revert':
        return withFlags(`git revert ${v || '<commit>'}`);
      case 'tag':
        return withFlags(`git tag ${v || '<tag-name>'}`);
      case 'remote':
        return withFlags(`git remote add ${remote} ${v || '<url>'}`);
      default:
        return '';
    }
  });
}
