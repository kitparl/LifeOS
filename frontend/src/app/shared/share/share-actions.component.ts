import { Component, computed, input, signal } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { copyText } from '../../core/utils/clipboard';
import { QrCodeComponent, qrPngBlob } from '../qr-code/qr-code.component';
import { ShareText, absoluteShareUrl, mailtoHref, whatsappHref } from './share-links';

/**
 * Invite: the full short URL, one primary Share button, and labelled icon buttons for
 * Copy / WhatsApp / Email / QR. The QR can itself be shared or saved as an image. Everything
 * runs in the browser and opens the person's own apps; nothing calls LifeOS.
 * The words come from the feature (`text`); test ids are `<testIdPrefix>-copy`, `-whatsapp`, ...
 */
@Component({
  selector: 'app-share-actions',
  standalone: true,
  imports: [LucideDynamicIcon, QrCodeComponent],
  template: `
    <div class="space-y-3">
      <div>
        <p class="mb-1 text-xs font-medium" style="color: var(--text-muted)">{{ text().heading }}</p>
        <p
          class="break-all rounded border border-[var(--xp-border)] px-2 py-1.5 text-sm font-medium"
          [attr.data-testid]="testIdPrefix() + '-share-url'"
        >{{ url() }}</p>
      </div>

      @if (canShare) {
        <button
          type="button"
          class="btn-primary inline-flex w-full items-center justify-center gap-2 text-sm sm:w-auto"
          [attr.data-testid]="testIdPrefix() + '-share'"
          (click)="share()"
        >
          <svg class="h-4 w-4" lucideIcon="share-2" aria-hidden="true"></svg>
          {{ text().shareLabel }}
        </button>
      }

      <div class="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <button type="button" class="btn-secondary inline-flex items-center justify-center gap-2 text-sm" [attr.data-testid]="testIdPrefix() + '-copy'" (click)="copy()">
          <svg class="h-4 w-4" lucideIcon="copy" aria-hidden="true"></svg>
          {{ copied() ? 'Copied!' : 'Copy link' }}
        </button>
        <a
          class="btn-secondary inline-flex items-center justify-center gap-2 text-sm"
          [attr.data-testid]="testIdPrefix() + '-whatsapp'"
          target="_blank"
          rel="noopener"
          [href]="whatsapp()"
        >
          <svg class="h-4 w-4" lucideIcon="message-circle" aria-hidden="true"></svg>
          WhatsApp
        </a>
        <a class="btn-secondary inline-flex items-center justify-center gap-2 text-sm" [attr.data-testid]="testIdPrefix() + '-email'" [href]="email()">
          <svg class="h-4 w-4" lucideIcon="mail" aria-hidden="true"></svg>
          Email
        </a>
        @if (qrMode() === 'toggle') {
          <button
            type="button"
            class="btn-secondary inline-flex items-center justify-center gap-2 text-sm"
            [attr.data-testid]="testIdPrefix() + '-qr-toggle'"
            [attr.aria-expanded]="qrOpen()"
            (click)="qrOpen.set(!qrOpen())"
          >
            <svg class="h-4 w-4" lucideIcon="qr-code" aria-hidden="true"></svg>
            {{ qrOpen() ? 'Hide QR' : 'QR code' }}
          </button>
        }
      </div>

      @if (qrMode() === 'shown' || qrOpen()) {
        <div class="flex flex-wrap items-end gap-3">
          <div class="inline-block rounded border border-[var(--xp-border)] bg-white p-1" [attr.data-testid]="testIdPrefix() + '-group-qr'">
            <app-qr-code [payload]="url()" [label]="'QR code for ' + name()" />
          </div>
          <div class="flex flex-col gap-2 text-sm">
            <p class="text-xs" style="color: var(--text-muted)">{{ text().qrHint }}</p>
            @if (canShareFiles) {
              <button type="button" class="btn-secondary inline-flex items-center gap-2 text-sm" [attr.data-testid]="testIdPrefix() + '-qr-share'" (click)="shareQr()">
                <svg class="h-4 w-4" lucideIcon="share-2" aria-hidden="true"></svg>
                Share QR
              </button>
            }
            <button type="button" class="btn-secondary inline-flex items-center gap-2 text-sm" [attr.data-testid]="testIdPrefix() + '-qr-download'" (click)="downloadQr()">
              <svg class="h-4 w-4" lucideIcon="download" aria-hidden="true"></svg>
              Download QR
            </button>
          </div>
        </div>
      }
    </div>
  `,
})
export class ShareActionsComponent {
  /** What is being shared (a group or trip name): used in the message and the QR file name. */
  readonly name = input.required<string>();
  readonly urlPath = input.required<string>();
  readonly text = input.required<ShareText>();
  readonly testIdPrefix = input.required<string>();
  /** `shown` on the create result; `toggle` elsewhere so the QR stays out of the way. */
  readonly qrMode = input<'shown' | 'toggle'>('toggle');

  readonly url = computed(() => absoluteShareUrl(this.urlPath()));
  private readonly subject = computed(() => this.text().subject(this.name()));
  private readonly message = computed(() => this.text().message(this.name(), this.url()));
  readonly whatsapp = computed(() => whatsappHref(this.message()));
  readonly email = computed(() => mailtoHref(this.subject(), this.message()));

  readonly copied = signal(false);
  readonly qrOpen = signal(false);
  readonly canShare = typeof navigator !== 'undefined' && typeof navigator.share === 'function';
  readonly canShareFiles =
    this.canShare &&
    typeof navigator.canShare === 'function' &&
    navigator.canShare({ files: [new File([''], 'qr.png', { type: 'image/png' })] });

  async copy(): Promise<void> {
    this.copied.set(await copyText(this.url()));
  }

  async share(): Promise<void> {
    await this.tryShare({ title: this.subject(), text: this.message(), url: this.url() });
  }

  async shareQr(): Promise<void> {
    const file = new File([await qrPngBlob(this.url())], this.fileName(), { type: 'image/png' });
    await this.tryShare({ title: this.subject(), text: this.message(), files: [file] });
  }

  async downloadQr(): Promise<void> {
    const href = URL.createObjectURL(await qrPngBlob(this.url()));
    const link = document.createElement('a');
    link.href = href;
    link.download = this.fileName();
    link.click();
    setTimeout(() => URL.revokeObjectURL(href), 1000);
  }

  private fileName(): string {
    const slug = this.name().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    return `${this.text().filePrefix}-${slug || 'link'}-qr.png`;
  }

  private async tryShare(data: ShareData): Promise<void> {
    try {
      await navigator.share(data);
    } catch {
      // Dismissed share sheet — nothing to do.
    }
  }
}
