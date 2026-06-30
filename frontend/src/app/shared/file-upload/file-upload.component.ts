import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { FilesService } from '../../features/files/services/files.service';

@Component({
  selector: 'app-file-upload',
  standalone: true,
  template: `
    <div class="space-y-2 text-sm">
      <input type="file" [accept]="accept" (change)="onSelect($event)" />
      @if (uploading) {
        <p class="text-xs text-gray-600">Uploading…</p>
      }
      @if (previewUrl) {
        <img [src]="previewUrl" alt="Preview" class="max-h-32 rounded border border-[var(--xp-border)]" />
      }
      @if (error) {
        <p class="text-xs text-red-700">{{ error }}</p>
      }
    </div>
  `,
})
export class FileUploadComponent {
  private readonly filesService = inject(FilesService);

  @Input() accept = 'image/*';
  @Input() module = 'general';
  @Input() entityId: string | null = null;
  @Output() uploaded = new EventEmitter<string>();

  uploading = false;
  previewUrl = '';
  error = '';

  onSelect(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    this.uploading = true;
    this.error = '';
    this.filesService.upload(file, this.module, this.entityId ?? undefined).subscribe({
      next: (record) => {
        this.previewUrl = this.filesService.contentUrl(record);
        this.uploaded.emit(this.previewUrl);
        this.uploading = false;
      },
      error: () => {
        this.error = 'Upload failed';
        this.uploading = false;
      },
    });
  }
}
