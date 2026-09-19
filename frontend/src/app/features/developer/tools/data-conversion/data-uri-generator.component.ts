import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';

@Component({
  selector: 'app-data-uri-generator-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="data-uri-generator"
      title="Data URI Generator"
      description="Generate a data: URI from a local file. The file is read locally and never uploaded."
      icon="link"
    >
      <div class="space-y-2 pb-3">
        <label class="form-label">File</label>
        <input class="input-field" type="file" (change)="onFileChange($event)" />
      </div>
      @if (fileName()) {
        <p class="pb-2 text-xs text-[var(--text-muted)]">{{ fileName() }} · {{ mimeType() }} · {{ dataUri().length }} chars</p>
      }
      @if (dataUri()) {
        <div class="flex items-start gap-2">
          <textarea class="input-field h-40 resize-y font-mono text-xs" readonly [ngModel]="dataUri()"></textarea>
          <app-copy-button [text]="dataUri()" />
        </div>
      } @else {
        <p class="text-sm text-[var(--text-muted)]">Choose a file above.</p>
      }
    </app-dev-tool-shell>
  `,
})
export class DataUriGeneratorToolComponent {
  readonly dataUri = signal('');
  readonly fileName = signal('');
  readonly mimeType = signal('');

  onFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    this.fileName.set(file.name);
    this.mimeType.set(file.type || 'application/octet-stream');
    const reader = new FileReader();
    reader.onload = () => this.dataUri.set(reader.result as string);
    reader.readAsDataURL(file);
  }
}
