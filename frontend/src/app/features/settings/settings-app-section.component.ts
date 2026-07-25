import { Component, inject, signal } from '@angular/core';
import { PwaService } from '../../core/services/pwa.service';

@Component({
  selector: 'app-settings-app-section',
  standalone: true,
  template: `
    <div class="space-y-3">
      <p class="text-sm text-[var(--text-muted)]">
        LifeOS updates itself when you reopen the app. Use these controls if the installed app is
        still showing an older version — on iPhone there is no browser reload button.
      </p>

      <div class="flex flex-wrap gap-2">
        <button type="button" class="btn-primary text-xs" [disabled]="checking()" (click)="checkForUpdate()">
          {{ checking() ? 'Checking…' : 'Check for updates' }}
        </button>
        <button type="button" class="btn-secondary text-xs" (click)="hardRefresh()">Force refresh</button>
      </div>

      @if (status(); as message) {
        <p class="text-sm" style="color: var(--text-muted)">{{ message }}</p>
      }

      <p class="text-xs" style="color: var(--text-muted)">
        Force refresh clears the offline cache and reloads from the server. Unsynced offline changes
        are kept, but the app will need the network to start.
      </p>
    </div>
  `,
})
export class SettingsAppSectionComponent {
  private readonly pwa = inject(PwaService);

  readonly checking = signal(false);
  readonly status = signal<string | null>(null);

  async checkForUpdate(): Promise<void> {
    this.checking.set(true);
    this.status.set(null);
    const found = await this.pwa.checkForUpdate();
    this.checking.set(false);
    this.status.set(
      found
        ? 'Update found — reloading…'
        : 'You are on the latest version. If the app still looks old, use Force refresh.',
    );
  }

  hardRefresh(): void {
    this.status.set('Clearing cache and reloading…');
    void this.pwa.hardRefresh();
  }
}
