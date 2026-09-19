import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';

@Component({
  selector: 'app-image-base64-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="image-base64"
      title="Image ↔ Base64"
      description="Convert a local image to a Base64 data URI, or preview a Base64/data URI string as an image. Files are read locally and never uploaded."
      icon="file-code"
    >
      <div class="grid gap-4 md:grid-cols-2">
        <div class="space-y-2">
          <label class="form-label">Image → Base64</label>
          <input class="input-field" type="file" accept="image/*" (change)="onFileChange($event)" />
          @if (dataUri()) {
            <div class="flex items-center gap-2">
              <textarea class="input-field h-28 resize-y font-mono text-xs" readonly [ngModel]="dataUri()"></textarea>
              <app-copy-button [text]="dataUri()" />
            </div>
            <img [src]="dataUri()" alt="Preview" class="max-h-40 rounded-[var(--radius-sm)] border border-[var(--border)]" />
          }
        </div>
        <div class="space-y-2">
          <label class="form-label">Base64 / data URI → Image</label>
          <textarea
            class="input-field h-28 resize-y font-mono text-xs"
            placeholder="data:image/png;base64,iVBORw0K..."
            [ngModel]="previewInput()"
            (ngModelChange)="previewInput.set($event)"
          ></textarea>
          @if (previewSrc()) {
            <img [src]="previewSrc()" alt="Preview" class="max-h-40 rounded-[var(--radius-sm)] border border-[var(--border)]" (error)="onPreviewError()" />
          }
          @if (previewError()) {
            <p class="text-xs text-[var(--danger)]">{{ previewError() }}</p>
          }
        </div>
      </div>
    </app-dev-tool-shell>
  `,
})
export class ImageBase64ToolComponent {
  readonly dataUri = signal('');
  readonly previewInput = signal('');
  readonly previewError = signal<string | null>(null);

  previewSrc(): string {
    const raw = this.previewInput().trim();
    if (!raw) return '';
    return raw.startsWith('data:') ? raw : `data:image/png;base64,${raw}`;
  }

  onFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => this.dataUri.set(reader.result as string);
    reader.readAsDataURL(file);
  }

  onPreviewError(): void {
    this.previewError.set('Could not render this as an image — check the Base64/data URI is valid.');
  }
}
