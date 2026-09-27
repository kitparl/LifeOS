import { Injectable, signal } from '@angular/core';

export interface ConfirmOptions {
  /** Accept button text (default "Delete"). */
  acceptLabel?: string;
  /** Red, destructive styling for the accept button (default true). */
  danger?: boolean;
}

/**
 * In-app confirmation (delete by default) for web, iPad, and phone.
 * On phone (max-width 640px) app-modal already becomes a full-screen sheet.
 */
@Injectable({ providedIn: 'root' })
export class ConfirmService {
  readonly open = signal(false);
  readonly title = signal('Confirm');
  readonly message = signal('');
  readonly acceptLabel = signal('Delete');
  readonly danger = signal(true);

  private pending: ((value: boolean) => void) | null = null;

  confirm(message: string, title = 'Confirm', options: ConfirmOptions = {}): Promise<boolean> {
    this.pending?.(false);
    return new Promise((resolve) => {
      this.pending = resolve;
      this.title.set(title);
      this.message.set(message);
      this.acceptLabel.set(options.acceptLabel ?? 'Delete');
      this.danger.set(options.danger ?? true);
      this.open.set(true);
    });
  }

  accept(): void {
    this.finish(true);
  }

  cancel(): void {
    this.finish(false);
  }

  private finish(value: boolean): void {
    this.open.set(false);
    const resolve = this.pending;
    this.pending = null;
    resolve?.(value);
  }
}
