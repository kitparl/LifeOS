import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ListPaginatorComponent } from '../../shared/pagination/list-paginator.component';
import { FileRecord } from './models/file.models';
import { FilesService } from './services/files.service';

@Component({
  selector: 'app-files-page',
  standalone: true,
  imports: [DatePipe, ListPaginatorComponent],
  template: `
    <div class="space-y-3">
      <h1 class="text-lg font-semibold">Files</h1>
      <p class="text-sm" style="color: var(--text-muted)">Uploaded files stored via the LifeOS files API.</p>

      @if (loading) {
        <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
      } @else if (total === 0) {
        <p class="text-sm" style="color: var(--text-muted)">No files uploaded yet.</p>
      } @else {
        <div class="panel !p-0 overflow-hidden">
          <ul class="divide-y divide-[var(--xp-border)] text-sm">
            @for (f of files; track f.id) {
              <li class="flex items-center justify-between gap-2 px-3 py-2">
                <div>
                  <button type="button" class="link text-left" (click)="open(f)">{{ f.filename }}</button>
                  <p class="text-xs text-gray-500">
                    {{ f.content_type }} · {{ formatSize(f.size_bytes) }} · {{ f.created_at | date: 'short' }}
                  </p>
                </div>
                <div class="flex gap-2">
                  <button type="button" class="btn-ghost text-xs" (click)="download(f)">Download</button>
                  <button type="button" class="text-xs" style="color: var(--danger)" (click)="remove(f.id)">Delete</button>
                </div>
              </li>
            }
          </ul>
          <app-list-paginator
            [total]="total"
            [pageSize]="pageSize"
            [currentPage]="currentPage"
            (pageChange)="setPage($event)"
          />
        </div>
      }
    </div>
  `,
})
export class FilesPageComponent implements OnInit {
  private readonly filesService = inject(FilesService);

  files: FileRecord[] = [];
  total = 0;
  loading = false;
  currentPage = 1;
  readonly pageSize = 25;

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    const offset = (this.currentPage - 1) * this.pageSize;
    this.filesService.list({ limit: this.pageSize, offset }).subscribe({
      next: (result) => {
        this.files = result.items;
        this.total = result.total;
        this.clampPage();
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }

  setPage(page: number): void {
    this.currentPage = page;
    this.load();
  }

  private clampPage(): void {
    const totalPages = Math.max(1, Math.ceil(this.total / this.pageSize));
    if (this.currentPage > totalPages) {
      this.currentPage = totalPages;
      this.load();
    }
  }

  open(f: FileRecord): void {
    this.filesService.openInNewTab(f.id);
  }

  download(f: FileRecord): void {
    this.filesService.saveAsDownload(f);
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
