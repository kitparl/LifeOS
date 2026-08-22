import { Component, EventEmitter, Input, Output, inject, signal } from '@angular/core';
import { IntegrationsService, GitHubSyncResponse } from '../integrations/services/integrations.service';

@Component({
  selector: 'app-github-sync-button',
  standalone: true,
  template: `
    <button
      type="button"
      [class]="buttonClass || 'kn-plus'"
      [attr.aria-label]="tooltip"
      [title]="tooltip"
      [disabled]="disabled || syncing() || !configured"
      data-testid="github-sync-button"
      (click)="sync()"
    >
      {{ syncing() ? '…' : '↗' }}
    </button>
  `,
})
export class GitHubSyncButtonComponent {
  private readonly integrations = inject(IntegrationsService);

  @Input() sectionId = '';
  @Input() disabled = false;
  @Input() configured = false;
  @Input() buttonClass = '';
  @Input() tooltip = 'Push to GitHub';
  @Input() beforeSync: (() => Promise<void> | void) | null = null;

  @Output() syncSuccess = new EventEmitter<string>();
  @Output() syncError = new EventEmitter<string>();

  readonly syncing = signal(false);

  async sync(): Promise<void> {
    if (this.syncing() || this.disabled || !this.configured || !this.sectionId) {
      return;
    }
    this.syncing.set(true);
    try {
      if (this.beforeSync) {
        await this.beforeSync();
      }
      this.integrations.syncSectionToGitHub(this.sectionId).subscribe({
        next: (res: GitHubSyncResponse) => {
          this.syncSuccess.emit(res.message);
          this.syncing.set(false);
        },
        error: (err: { error?: { detail?: string } }) => {
          const message = err?.error?.detail || 'GitHub sync failed';
          this.syncError.emit(typeof message === 'string' ? message : 'GitHub sync failed');
          this.syncing.set(false);
        },
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Save before syncing';
      this.syncError.emit(message);
      this.syncing.set(false);
    }
  }
}
