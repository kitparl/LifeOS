import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FileRecord } from './models/file.models';
import { FilesService } from './services/files.service';

@Component({
  selector: 'app-files-page',
  standalone: true,
  imports: [DatePipe],
  template: `
    <div class="space-y-3">
      <h1 class="text-lg font-semibold">Files</h1>
      <p class="text-sm text-gray-600">Uploaded files stored in S3 (or local storage in dev).</p>

      @if (loading) {
        <p class="text-sm text-gray-600">Loading…</p>
      } @else if (files.length === 0) {
        <p class="text-sm text-gray-600">No files uploaded yet.</p>
      } @else {
        <div class="panel !p-0 overflow-hidden">
          <ul class="divide-y divide-[var(--xp-border)] text-sm">
            @for (f of files; track f.id) {
              <li class="flex items-center justify-between gap-2 px-3 py-2">
                <div>
                  <a [href]="contentUrl(f)" target="_blank" class="text-[var(--xp-blue)] underline">{{ f.filename }}</a>
                  <p class="text-xs text-gray-500">
                    {{ f.content_type }} · {{ formatSize(f.size_bytes) }} · {{ f.created_at | date: 'short' }}
                  </p>
                </div>
                <button type="button" class="text-xs text-red-700" (click)="remove(f.id)">Delete</button>
              </li>
            }
          </ul>
        </div>
      }
    </div>
  `,
})
export class FilesPageComponent implements OnInit {
  private readonly filesService = inject(FilesService);

  files: FileRecord[] = [];
  loading = false;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.filesService.list().subscribe({
      next: (data) => {
        this.files = data;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }

  contentUrl(f: FileRecord): string {
    return this.filesService.contentUrl(f);
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  remove(id: string): void {
    this.filesService.delete(id).subscribe({ next: () => this.load() });
  }
}
