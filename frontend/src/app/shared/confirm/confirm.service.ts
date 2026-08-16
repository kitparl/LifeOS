import { Injectable, signal } from '@angular/core';

/**
 * Phone (max-width 640px): native window.confirm.
 * Web + iPad: app-modal via ConfirmHostComponent in AppShell.
 */
@Injectable({ providedIn: 'root' })
export class ConfirmService {
  readonly open = signal(false);
  readonly title = signal('Confirm');
  readonly message = signal('');

  private pending: ((value: boolean) => void) | null = null;

  confirm(message: string, title = 'Confirm'): Promise<boolean> {
    if (typeof window !== 'undefined' && window.matchMedia('(max-width: 640px)').matches) {
      return Promise.resolve(window.confirm(message));
    }
    this.pending?.(false);
    return new Promise((resolve) => {
      this.pending = resolve;
      this.title.set(title);
      this.message.set(message);
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
