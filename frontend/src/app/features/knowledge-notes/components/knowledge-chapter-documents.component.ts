import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { DocumentViewerService } from '../../../shared/document-viewer/document-viewer.service';
import { FilesService } from '../../files/services/files.service';
import {
  KnowledgeChapterDocument,
  KnowledgeChapterDocumentsGroup,
} from '../models/knowledge-notes.models';

@Component({
  selector: 'app-knowledge-chapter-documents',
  standalone: true,
  imports: [DatePipe],
  host: { class: 'contents' },
  template: `
    <section class="kn-main kn-docs" data-testid="kn-chapter-documents">
      <div class="kn-docbar">
        <h2 class="kn-section-title-read">{{ heading }}</h2>
        <div class="kn-docbar__actions">
          @if (chapterFilter) {
            <button type="button" class="btn-ghost text-xs" (click)="showAll.emit()">All chapters</button>
          }
          <button type="button" class="btn-secondary text-xs" (click)="close.emit()">Back to note</button>
        </div>
      </div>

      @if (error) {
        <p class="text-xs" style="color: var(--danger)">{{ error }}</p>
      }

      @if (loading) {
        <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
      } @else if (groups.length === 0) {
        <div class="empty-state">
          <div class="empty-state__icon">📄</div>
          <p class="empty-state__title">No chapters</p>
          <p class="empty-state__desc">Add a chapter to collect PDF and Word documents from its notes.</p>
        </div>
      } @else {
        @for (group of groups; track group.chapter_id) {
          <div class="panel !p-0 overflow-hidden" data-testid="kn-chapter-documents-group">
            <div class="title-bar rounded-none border-x-0 border-t-0">{{ group.chapter_title }}</div>
            @if (group.documents.length === 0) {
              <p class="p-3 text-sm" style="color: var(--text-muted)">
                No PDF or Word documents in this chapter.
              </p>
            } @else {
              <ul class="divide-y divide-[var(--xp-border)] text-sm">
                @for (doc of group.documents; track doc.id) {
                  <li class="flex items-center justify-between gap-2 px-3 py-2">
                    <div class="min-w-0">
                      <button type="button" class="link text-left" (click)="view(doc)">{{ doc.filename }}</button>
                      <p class="text-xs" style="color: var(--text-muted)">
                        <button
                          type="button"
                          class="link"
                          (click)="openSection.emit({ sectionId: doc.section_id, chapterId: doc.chapter_id })"
                        >{{ doc.section_title }}</button>
                        · {{ formatSize(doc.size_bytes) }} · {{ doc.created_at | date: 'short' }}
                      </p>
                    </div>
                    <div class="flex shrink-0 gap-2">
                      <button
                        type="button"
                        class="btn-ghost text-xs"
                        data-testid="kn-chapter-document-view"
                        (click)="view(doc)"
                      >View</button>
                      <button
                        type="button"
                        class="text-xs"
                        style="color: var(--danger)"
                        data-testid="kn-chapter-document-delete"
                        (click)="remove(doc)"
                      >Delete</button>
                    </div>
                  </li>
                }
              </ul>
            }
          </div>
        }
      }
    </section>
  `,
})
export class KnowledgeChapterDocumentsComponent {
  private readonly filesService = inject(FilesService);
  private readonly confirm = inject(ConfirmService);
  private readonly documentViewer = inject(DocumentViewerService);

  @Input() groups: KnowledgeChapterDocumentsGroup[] = [];
  @Input() loading = false;
  @Input() error = '';
  @Input() chapterFilter: string | null = null;

  @Output() readonly removed = new EventEmitter<KnowledgeChapterDocument>();
  @Output() readonly showAll = new EventEmitter<void>();
  @Output() readonly close = new EventEmitter<void>();
  @Output() readonly openSection = new EventEmitter<{ sectionId: string; chapterId: string }>();

  get heading(): string {
    if (!this.chapterFilter) return 'Documents';
    return this.groups[0]?.chapter_title ? `${this.groups[0].chapter_title} documents` : 'Chapter documents';
  }

  view(doc: KnowledgeChapterDocument): void {
    this.documentViewer.open({
      documentId: doc.id,
      fileName: doc.filename,
      mimeType: doc.content_type,
    });
  }

  remove(doc: KnowledgeChapterDocument): void {
    void this.removeConfirmed(doc);
  }

  private async removeConfirmed(doc: KnowledgeChapterDocument): Promise<void> {
    const ok = await this.confirm.confirm(
      `Remove “${doc.filename}”? This deletes the file. It will no longer be available here.`,
      'Remove file'
    );
    if (!ok) return;
    this.filesService.delete(doc.id).subscribe({
      next: () => this.removed.emit(doc),
    });
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
}
