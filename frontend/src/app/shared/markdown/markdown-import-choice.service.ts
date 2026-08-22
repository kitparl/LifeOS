import { Injectable, signal } from '@angular/core';

export type MarkdownImportChoice = 'replace' | 'append' | 'cancel';

@Injectable({ providedIn: 'root' })
export class MarkdownImportChoiceService {
  readonly open = signal(false);
  readonly message = signal('');

  private pending: ((value: MarkdownImportChoice) => void) | null = null;

  choose(message: string): Promise<MarkdownImportChoice> {
    this.pending?.('cancel');
    return new Promise((resolve) => {
      this.pending = resolve;
      this.message.set(message);
      this.open.set(true);
    });
  }

  pick(choice: MarkdownImportChoice): void {
    this.open.set(false);
    const resolve = this.pending;
    this.pending = null;
    resolve?.(choice);
  }
}
