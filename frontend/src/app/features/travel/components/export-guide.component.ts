import { Component, inject, input, signal } from '@angular/core';
import { apiErrorMessage } from '../../../core/utils/http';
import { TravelApiService } from '../services/travel-api.service';

/** "Share as PDF" for a trip or an adventure: downloads a friendly, tappable guide a friend can read without the app. */
@Component({
  selector: 'app-export-guide',
  standalone: true,
  template: `
    <button
      type="button"
      class="btn-secondary text-xs"
      [disabled]="busy()"
      title="Download a PDF guide you can share with friends"
      (click)="$event.stopPropagation(); download()"
      (keydown.enter)="$event.stopPropagation()"
    >
      {{ busy() ? 'Preparing PDF…' : '📄 Share as PDF' }}
    </button>
    @if (error()) {
      <span class="text-xs" style="color: var(--danger)">{{ error() }}</span>
    }
  `,
})
export class ExportGuideComponent {
  private readonly api = inject(TravelApiService);

  readonly kind = input.required<'trips' | 'adventures'>();
  readonly id = input.required<string>();
  readonly name = input.required<string>();
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);

  download(): void {
    this.busy.set(true);
    this.error.set(null);
    this.api.exportGuide(this.kind(), this.id()).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${this.fileName()}.pdf`;
        link.click();
        URL.revokeObjectURL(url);
        this.busy.set(false);
      },
      error: (err) => {
        this.busy.set(false);
        this.error.set(apiErrorMessage(err, 'Could not create the PDF'));
      },
    });
  }

  private fileName(): string {
    const slug = this.name().replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-+|-+$/g, '');
    return `${slug || 'travel'}-guide`;
  }
}
