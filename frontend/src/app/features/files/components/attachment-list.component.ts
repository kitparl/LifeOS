import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, inject } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { filesFromClipboard, filesFromDataTransfer } from '../../../shared/file-upload/clipboard-files';
import { fileFingerprint, sha256Hex } from '../../../shared/file-upload/file-hash';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { FileRecord } from '../models/file.models';
import { FilesService } from '../services/files.service';

@Component({
  selector: 'app-attachment-list',
  standalone: true,
  imports: [DatePipe, ModalComponent],
  template: `
    <div class="panel !p-0 overflow-hidden">
      <div class="title-bar rounded-none border-x-0 border-t-0">{{ title }}</div>
      <div class="space-y-2 p-3">
        @if (allowUpload) {
        <div
          class="flex flex-col items-center justify-center gap-2 rounded border border-dashed px-3 py-4 text-center outline-none transition-colors"
          tabindex="0"
          [style.border-color]="dragOver ? 'var(--xp-blue)' : 'var(--xp-border)'"
          [style.background]="
            dragOver
              ? 'color-mix(in srgb, var(--xp-blue) 12%, transparent)'
              : 'color-mix(in srgb, var(--primary-soft) 35%, transparent)'
          "
          [class.opacity-60]="uploading || !entityId"
          (paste)="onPaste($event)"
          (dragover)="onDragOver($event)"
          (dragleave)="onDragLeave($event)"
          (drop)="onDrop($event)"
        >
          <p class="text-sm font-medium">Upload files</p>
          <p class="text-xs" style="color: var(--text-muted)">
            Images, PDF, docs — choose, paste (Ctrl/Cmd+V), or drop (multiple OK)
          </p>
          <input
            #fileInput
            type="file"
            class="hidden"
            multiple
            (change)="onSelect($event)"
            [disabled]="uploading || !entityId"
          />
          <button
            type="button"
            class="btn-primary text-xs"
            [disabled]="uploading || !entityId"
            (click)="fileInput.click()"
          >
            {{ uploading ? 'Uploading…' : 'Add files' }}
          </button>
          @if (error) {
            <p class="text-xs" style="color: var(--danger)">{{ error }}</p>
          }
        </div>
        }

        @if (loading) {
          <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
        } @else if (files.length === 0) {
          <p class="text-sm" style="color: var(--text-muted)">{{ emptyText }}</p>
        } @else {
          <ul class="divide-y divide-[var(--xp-border)] text-sm">
            @for (f of files; track f.id) {
              <li class="flex items-center justify-between gap-2 py-2">
                <div class="min-w-0">
                  <button type="button" class="link text-left" (click)="enablePreview ? preview(f) : open(f)">{{ f.filename }}</button>
                  <p class="text-xs" style="color: var(--text-muted)">
                    {{ f.content_type }} · {{ formatSize(f.size_bytes) }} · {{ f.created_at | date: 'short' }}
                  </p>
                  @if (previewUrl[f.id] && isImage(f)) {
                    <button type="button" class="mt-1 block" (click)="enablePreview ? preview(f) : open(f)">
                      <img
                        [src]="previewUrl[f.id]"
                        alt=""
                        class="max-h-24 rounded border border-[var(--xp-border)]"
                      />
                    </button>
                  }
                </div>
                <div class="flex shrink-0 gap-2">
                  @if (enablePreview) {
                    <button type="button" class="btn-ghost text-xs" (click)="preview(f)">Preview</button>
                  }
                  <button type="button" class="btn-ghost text-xs" (click)="download(f)">Download</button>
                  <button type="button" class="text-xs" style="color: var(--danger)" (click)="remove(f.id)">
                    Remove
                  </button>
                </div>
              </li>
            }
          </ul>
        }
      </div>
    </div>

    <app-modal
      [open]="!!previewing"
      [title]="previewing?.filename ?? 'Preview'"
      [maxWidth]="'880px'"
      [maximizable]="true"
      [hasFooter]="true"
      (closed)="closePreview()"
    >
      <div body>
        @if (previewing) {
          @if (isImage(previewing) && previewSrc) {
            <img
              [src]="previewSrc"
              [alt]="previewing.filename"
              style="display:block;margin:0 auto;max-width:100%;max-height:70vh"
            />
          } @else if (isPdf(previewing) && previewFrame) {
            <iframe
              [src]="previewFrame"
              [title]="previewing.filename"
              style="width:100%;height:70vh;border:0"
            ></iframe>
          } @else {
            <p class="text-sm" style="color: var(--text-muted)">No inline preview for this file type. Open it in a new tab or download it.</p>
          }
        }
      </div>
      <div footer class="flex flex-wrap justify-end gap-2">
        @if (previewing) {
          <button type="button" class="btn-ghost text-xs" (click)="open(previewing)">Open</button>
          <button type="button" class="btn-secondary text-xs" (click)="download(previewing)">Download</button>
        }
      </div>
    </app-modal>
  `,
})
export class AttachmentListComponent implements OnChanges {
  private readonly filesService = inject(FilesService);
  private readonly confirm = inject(ConfirmService);
  private readonly sanitizer = inject(DomSanitizer);

  @Input({ required: true }) module!: string;
  @Input() entityId: string | null = null;
  @Input() title = 'Attachments';
  @Input() emptyText = 'No attachments yet.';
  @Input() allowUpload = true;
  @Input() enablePreview = false;
  @Output() removed = new EventEmitter<FileRecord>();
  @Output() uploaded = new EventEmitter<FileRecord>();

  files: FileRecord[] = [];
  loading = false;
  uploading = false;
  dragOver = false;
  error = '';
  previewUrl: Record<string, string> = {};
  previewing: FileRecord | null = null;
  previewSrc: string | null = null;
  previewFrame: SafeResourceUrl | null = null;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['entityId'] || changes['module']) {
      this.load();
    }
  }

  load(): void {
    if (!this.entityId) {
      this.files = [];
      return;
    }
    this.loading = true;
    this.filesService.list(this.module, this.entityId).subscribe({
      next: (data) => {
        this.files = data;
        this.loading = false;
        for (const f of data) {
          if (this.isImage(f) && !this.previewUrl[f.id]) {
            this.filesService.tokenUrl(f.id).subscribe({
              next: (url) => (this.previewUrl[f.id] = url),
            });
          }
        }
      },
      error: () => (this.loading = false),
    });
  }

  onSelect(event: Event): void {
    const input = event.target as HTMLInputElement;
    const files = input.files ? Array.from(input.files) : [];
    input.value = '';
    void this.uploadFiles(files);
  }

  onPaste(event: ClipboardEvent): void {
    if (!this.entityId || this.uploading) return;
    const files = filesFromClipboard(event);
    if (!files.length) return;
    event.preventDefault();
    event.stopPropagation();
    void this.uploadFiles(files);
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    if (this.entityId) this.dragOver = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.dragOver = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragOver = false;
    void this.uploadFiles(filesFromDataTransfer(event.dataTransfer));
  }

  private async uploadFiles(files: File[]): Promise<void> {
    if (!this.entityId || !files.length) return;
    this.uploading = true;
    this.error = '';
    const knownChecksums = new Set(
      this.files.map((f) => (f.checksum_sha256 || '').toLowerCase()).filter(Boolean),
    );
    const knownNames = new Set(this.files.map((f) => f.filename.toLowerCase()));
    const batchSeen = new Set<string>();

    for (const file of files) {
      const fp = fileFingerprint(file);
      if (batchSeen.has(fp) || knownNames.has(file.name.toLowerCase())) {
        this.error = 'This file has already been uploaded';
        this.uploading = false;
        return;
      }
      batchSeen.add(fp);

      try {
        const checksum = await sha256Hex(file);
        if (knownChecksums.has(checksum)) {
          this.error = 'This file has already been uploaded';
          this.uploading = false;
          return;
        }
      } catch {
        // Server still enforces content duplicates.
      }

      try {
        await new Promise<void>((resolve, reject) => {
          this.filesService.upload(file, this.module, this.entityId!).subscribe({
            next: (record) => {
              if (record.checksum_sha256) knownChecksums.add(record.checksum_sha256.toLowerCase());
              knownNames.add(record.filename.toLowerCase());
              this.uploaded.emit(record);
              resolve();
            },
            error: (err) => reject(err),
          });
        });
      } catch (err: unknown) {
        const detail = (err as { error?: { detail?: string } })?.error?.detail;
        this.error = detail || 'Upload failed';
        this.uploading = false;
        this.load();
        return;
      }
    }
    this.uploading = false;
    this.load();
  }

  open(f: FileRecord): void {
    this.filesService.openInNewTab(f.id);
  }

  isImage(f: FileRecord): boolean {
    return f.content_type.startsWith('image/');
  }

  isPdf(f: FileRecord): boolean {
    return f.content_type === 'application/pdf' || /\.pdf$/i.test(f.filename);
  }

  preview(f: FileRecord): void {
    this.previewing = f;
    this.previewSrc = this.previewUrl[f.id] ?? null;
    this.previewFrame = this.previewSrc && this.isPdf(f)
      ? this.sanitizer.bypassSecurityTrustResourceUrl(this.previewSrc)
      : null;
    this.filesService.tokenUrl(f.id).subscribe({
      next: (url) => {
        if (this.previewing?.id !== f.id) return;
        this.previewUrl[f.id] = url;
        this.previewSrc = url;
        this.previewFrame = this.isPdf(f) ? this.sanitizer.bypassSecurityTrustResourceUrl(url) : null;
      },
    });
  }

  closePreview(): void {
    this.previewing = null;
    this.previewSrc = null;
    this.previewFrame = null;
  }

  download(f: FileRecord): void {
    this.filesService.saveAsDownload(f);
  }

  remove(id: string): void {
    void this.removeConfirmed(id);
  }

  private async removeConfirmed(id: string): Promise<void> {
    const file = this.files.find((f) => f.id === id);
    const ok = await this.confirm.confirm(
      `Remove “${file?.filename ?? 'this file'}”? This deletes the file. It will no longer be available here.`,
      'Remove file'
    );
    if (!ok) return;
    this.filesService.delete(id).subscribe({
      next: () => {
        if (file) this.removed.emit(file);
        this.load();
      },
    });
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
}
