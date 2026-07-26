import { Component, EventEmitter, Input, OnChanges, OnDestroy, Output, SimpleChanges, inject } from '@angular/core';
import { FilesService } from '../../features/files/services/files.service';
import { fileMatchesAccept, filesFromClipboard, filesFromDataTransfer, filterAccepted } from './clipboard-files';
import { fileFingerprint, sha256Hex } from './file-hash';

@Component({
  selector: 'app-file-upload',
  standalone: true,
  template: `
    <div
      class="space-y-2 text-sm outline-none"
      tabindex="0"
      (paste)="onPaste($event)"
      (dragover)="onDragOver($event)"
      (dragleave)="onDragLeave($event)"
      (drop)="onDrop($event)"
    >
      <div
        class="flex flex-col items-center justify-center gap-2 rounded border border-dashed px-3 py-4 text-center transition-colors"
        [style.border-color]="dragOver ? 'var(--xp-blue)' : 'var(--xp-border)'"
        [style.background]="
          dragOver
            ? 'color-mix(in srgb, var(--xp-blue) 12%, transparent)'
            : 'color-mix(in srgb, var(--primary-soft) 35%, transparent)'
        "
        [class.opacity-60]="uploading"
      >
        <p class="text-sm font-medium">{{ label }}</p>
        <p class="text-xs" style="color: var(--text-muted)">{{ hint }}</p>
        <input
          #fileInput
          type="file"
          class="hidden"
          [accept]="accept"
          [multiple]="multiple"
          (change)="onSelect($event)"
          [disabled]="uploading"
        />
        <div class="flex flex-wrap items-center justify-center gap-2">
          <button
            type="button"
            class="btn-primary text-xs"
            [disabled]="uploading"
            (click)="fileInput.click()"
          >
            {{ uploading ? 'Uploading…' : multiple ? 'Add files' : 'Choose file' }}
          </button>
          @if (!multiple && (previewUrl || valueUrl)) {
            <button type="button" class="btn-ghost text-xs" [disabled]="uploading" (click)="clear()">
              Remove
            </button>
          }
        </div>
        <p class="text-[11px]" style="color: var(--text-muted)">
          Tip: click this area, then paste (Ctrl/Cmd+V) any accepted file — or drop files here
        </p>
      </div>

      @if (!multiple && previewUrl) {
        @if (isImagePreview) {
          <img
            [src]="previewUrl"
            alt="Preview"
            class="max-h-40 w-auto rounded border border-[var(--xp-border)]"
          />
        } @else {
          <p class="text-xs" style="color: var(--text-muted)">
            File ready:
            <a [href]="previewUrl" target="_blank" rel="noopener" class="link">{{ pendingName || 'Open' }}</a>
          </p>
        }
      }
      @if (multiple && (pendingPreview || pendingName)) {
        @if (pendingPreview) {
          <img
            [src]="pendingPreview"
            alt="Uploading preview"
            class="max-h-24 w-auto rounded border border-[var(--xp-border)] opacity-80"
          />
        } @else {
          <p class="text-xs" style="color: var(--text-muted)">Uploading {{ pendingName }}…</p>
        }
      }
      @if (error) {
        <p class="text-xs" style="color: var(--danger)">{{ error }}</p>
      }
    </div>
  `,
})
export class FileUploadComponent implements OnChanges, OnDestroy {
  private readonly filesService = inject(FilesService);
  private localObjectUrl: string | null = null;

  @Input() label = 'Upload file';
  @Input() hint = 'Images, PDF, and documents — choose, paste, or drop';
  @Input() accept = 'image/*,application/pdf,text/plain,text/markdown,text/csv,.doc,.docx,.xls,.xlsx,.ppt,.pptx,audio/*';
  @Input() module = 'general';
  @Input() entityId: string | null = null;
  /** When true, each upload appends (emit + reset) instead of replacing a single value. */
  @Input() multiple = false;
  /** Existing stored URL when editing (files API path or external URL). Ignored when multiple. */
  @Input() initialUrl: string | null = null;
  /** SHA-256 hex digests already present (e.g. gallery photos) — blocks re-upload with an error. */
  @Input() knownChecksums: string[] = [];
  @Output() uploaded = new EventEmitter<string>();
  @Output() cleared = new EventEmitter<void>();

  uploading = false;
  dragOver = false;
  previewUrl = '';
  pendingPreview = '';
  pendingName = '';
  valueUrl = '';
  isImagePreview = true;
  error = '';

  private readonly sessionFingerprints = new Set<string>();
  private readonly sessionChecksums = new Set<string>();

  ngOnChanges(changes: SimpleChanges): void {
    if (!this.multiple && changes['initialUrl'] && this.initialUrl && !this.uploading) {
      this.applyStoredUrl(this.initialUrl);
    }
    if (changes['knownChecksums']) {
      // Rebuild from parent so removing a gallery item allows re-upload.
      this.sessionChecksums.clear();
      for (const c of this.knownChecksums) {
        if (c) this.sessionChecksums.add(c.toLowerCase());
      }
      this.sessionFingerprints.clear();
    }
  }

  ngOnDestroy(): void {
    this.revokeLocalPreview();
  }

  onSelect(event: Event): void {
    const input = event.target as HTMLInputElement;
    const files = input.files ? Array.from(input.files) : [];
    input.value = '';
    this.handleFiles(files);
  }

  onPaste(event: ClipboardEvent): void {
    const files = filterAccepted(filesFromClipboard(event), this.accept);
    if (!files.length) return;
    event.preventDefault();
    event.stopPropagation();
    this.handleFiles(files);
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.dragOver = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.dragOver = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.dragOver = false;
    const files = filterAccepted(filesFromDataTransfer(event.dataTransfer), this.accept);
    this.handleFiles(files);
  }

  clear(): void {
    this.revokeLocalPreview();
    this.previewUrl = '';
    this.pendingPreview = '';
    this.pendingName = '';
    this.valueUrl = '';
    this.error = '';
    this.cleared.emit();
  }

  private handleFiles(files: File[]): void {
    if (!files.length) return;
    const accepted = files.filter((f) => fileMatchesAccept(f, this.accept));
    if (!accepted.length) {
      this.error = 'That file type is not accepted here';
      return;
    }
    if (this.multiple) {
      void this.uploadMany(accepted);
    } else {
      void this.uploadFileAsync(accepted[0]);
    }
  }

  private async uploadMany(files: File[]): Promise<void> {
    const seen = new Set<string>();
    for (const file of files) {
      const fp = fileFingerprint(file);
      if (seen.has(fp)) {
        this.error = 'This file has already been uploaded';
        continue;
      }
      seen.add(fp);
      await this.uploadFileAsync(file);
    }
  }

  private async uploadFileAsync(file: File): Promise<void> {
    const fingerprint = fileFingerprint(file);
    if (this.sessionFingerprints.has(fingerprint)) {
      this.error = 'This file has already been uploaded';
      return;
    }

    let checksum = '';
    try {
      checksum = await sha256Hex(file);
    } catch {
      // Fall through — server still enforces duplicates.
    }
    if (checksum && this.sessionChecksums.has(checksum)) {
      this.error = 'This file has already been uploaded';
      return;
    }
    for (const known of this.knownChecksums) {
      if (known && checksum && known.toLowerCase() === checksum) {
        this.error = 'This file has already been uploaded';
        return;
      }
    }

    return new Promise((resolve) => {
      this.uploading = true;
      this.error = '';
      this.showLocalPreview(file);

      this.filesService.upload(file, this.module, this.entityId ?? undefined).subscribe({
        next: (record) => {
          this.sessionFingerprints.add(fingerprint);
          const recordSum = (record.checksum_sha256 || checksum).toLowerCase();
          if (recordSum) this.sessionChecksums.add(recordSum);
          const stable = this.filesService.contentUrl(record);
          this.uploaded.emit(stable);
          if (this.multiple) {
            this.revokeLocalPreview();
            this.pendingPreview = '';
            this.pendingName = '';
            this.previewUrl = '';
            this.valueUrl = '';
            this.uploading = false;
            resolve();
            return;
          }
          this.valueUrl = stable;
          this.isImagePreview = record.content_type.startsWith('image/');
          this.pendingName = record.filename;
          this.filesService.tokenUrl(record.id).subscribe({
            next: (url) => {
              this.revokeLocalPreview();
              this.previewUrl = url;
              this.uploading = false;
              resolve();
            },
            error: () => {
              this.uploading = false;
              resolve();
            },
          });
        },
        error: (err) => {
          this.error = err?.error?.detail || 'Upload failed';
          this.uploading = false;
          this.revokeLocalPreview();
          this.pendingPreview = '';
          this.pendingName = '';
          if (!this.multiple) {
            this.previewUrl = this.valueUrl;
          }
          resolve();
        },
      });
    });
  }

  private showLocalPreview(file: File): void {
    this.revokeLocalPreview();
    this.pendingName = file.name;
    this.isImagePreview = file.type.startsWith('image/');
    if (this.isImagePreview) {
      this.localObjectUrl = URL.createObjectURL(file);
      if (this.multiple) {
        this.pendingPreview = this.localObjectUrl;
      } else {
        this.previewUrl = this.localObjectUrl;
      }
    } else {
      this.pendingPreview = '';
      if (!this.multiple) {
        this.previewUrl = '';
      }
    }
  }

  private revokeLocalPreview(): void {
    if (this.localObjectUrl) {
      URL.revokeObjectURL(this.localObjectUrl);
      this.localObjectUrl = null;
    }
  }

  private applyStoredUrl(url: string): void {
    this.valueUrl = url;
    const fileId = this.extractFileId(url);
    if (fileId) {
      const looksPdf = /\.pdf(\?|$)/i.test(url);
      this.isImagePreview = !looksPdf;
      this.filesService.tokenUrl(fileId).subscribe({
        next: (tokenUrl) => {
          this.previewUrl = tokenUrl;
          this.isImagePreview = !looksPdf;
        },
        error: () => {
          this.previewUrl = url;
        },
      });
    } else {
      this.previewUrl = url;
      this.isImagePreview = /\.(png|jpe?g|gif|webp)(\?|$)/i.test(url) || url.startsWith('data:image');
    }
  }

  private extractFileId(url: string): string | null {
    const match = url.match(/\/files\/([0-9a-f-]{36})\/content/i);
    return match?.[1] ?? null;
  }
}
