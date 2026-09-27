import { Component, computed, input, signal } from '@angular/core';
import { copyText } from '../../../core/utils/clipboard';
import { QrCodeComponent } from '../../../shared/qr-code/qr-code.component';
import { absoluteShareUrl, mailtoHref, shareMessage, whatsappHref } from '../utils/share-links';

/**
 * The full short URL plus Copy, WhatsApp, Email, Share (when the browser has a share
 * sheet) and the group QR. Everything opens the person's own apps; nothing calls LifeOS.
 */
@Component({
  selector: 'app-split-share-actions',
  standalone: true,
  imports: [QrCodeComponent],
  template: `
    <div class="space-y-2">
      <p class="break-all text-sm font-medium" data-testid="split-share-url">{{ url() }}</p>
      <div class="flex flex-wrap items-center gap-2 text-xs">
        <button type="button" class="btn-secondary text-xs" data-testid="split-copy" (click)="copy()">
          {{ copied() ? 'Copied' : 'Copy' }}
        </button>
        <a
          class="btn-secondary text-xs"
          data-testid="split-whatsapp"
          target="_blank"
          rel="noopener"
          [href]="whatsapp()"
        >WhatsApp</a>
        <a class="btn-secondary text-xs" data-testid="split-email" [href]="email()">Email</a>
        @if (canShare) {
          <button type="button" class="btn-secondary text-xs" data-testid="split-share" (click)="share()">
            Share
          </button>
        }
        @if (qrMode() === 'toggle') {
          <button type="button" class="btn-ghost text-xs" data-testid="split-qr-toggle" (click)="qrOpen.set(!qrOpen())">
            {{ qrOpen() ? 'Hide QR' : 'QR' }}
          </button>
        }
      </div>
      @if (qrMode() === 'shown' || qrOpen()) {
        <div class="inline-block rounded border border-[var(--xp-border)] bg-white p-1" data-testid="split-group-qr">
          <app-qr-code [payload]="url()" [label]="'QR code for ' + groupName()" />
        </div>
      }
    </div>
  `,
})
export class SplitShareActionsComponent {
  readonly groupName = input.required<string>();
  readonly urlPath = input.required<string>();
  /** `shown` on the create result and group header; `toggle` on each on-device row. */
  readonly qrMode = input<'shown' | 'toggle'>('shown');

  readonly url = computed(() => absoluteShareUrl(this.urlPath()));
  private readonly message = computed(() => shareMessage(this.groupName(), this.url()));
  readonly whatsapp = computed(() => whatsappHref(this.message()));
  readonly email = computed(() => mailtoHref(this.groupName(), this.message()));

  readonly copied = signal(false);
  readonly qrOpen = signal(false);
  readonly canShare = typeof navigator !== 'undefined' && typeof navigator.share === 'function';

  async copy(): Promise<void> {
    this.copied.set(await copyText(this.url()));
  }

  async share(): Promise<void> {
    try {
      await navigator.share({ title: this.groupName(), text: this.message(), url: this.url() });
    } catch {
      // Dismissed share sheet — nothing to do.
    }
  }
}
