import { Component, Input } from '@angular/core';
import { copyText } from './clipboard.util';

@Component({
  selector: 'app-copy-button',
  standalone: true,
  template: `
    <button type="button" class="btn-secondary" [disabled]="!text" (click)="copy()">
      {{ copied ? 'Copied!' : label }}
    </button>
  `,
})
export class CopyButtonComponent {
  @Input() text = '';
  @Input() label = 'Copy';

  copied = false;
  private resetTimer: ReturnType<typeof setTimeout> | undefined;

  async copy(): Promise<void> {
    if (!this.text) return;
    const ok = await copyText(this.text);
    if (!ok) return;
    this.copied = true;
    clearTimeout(this.resetTimer);
    this.resetTimer = setTimeout(() => (this.copied = false), 1500);
  }
}
