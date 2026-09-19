import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { ModalComponent } from '../modal/modal.component';
import { UniversalDocumentViewerComponent } from './components/universal-document-viewer/universal-document-viewer.component';
import { DocumentViewerService } from './document-viewer.service';
import { PreviewType } from './models/document-preview.model';
import { DocumentPreviewApiService } from './services/document-preview-api.service';

const PREVIEW_TYPE_ICON: Record<PreviewType, string> = {
  pdf: 'file-text',
  image: 'image',
  text: 'file-text',
  csv: 'table',
  markdown: 'file-text',
  video: 'film',
  audio: 'music',
  unsupported: 'file-question',
};

@Component({
  selector: 'app-document-viewer-host',
  standalone: true,
  imports: [ModalComponent, UniversalDocumentViewerComponent, LucideDynamicIcon],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <app-modal
      [open]="viewer.isOpen()"
      [title]="title()"
      [maximizable]="true"
      maxWidth="880px"
      (closed)="viewer.close()"
    >
      <div titleIcon class="doc-viewer-host__icon">
        <svg [lucideIcon]="icon()" aria-hidden="true"></svg>
      </div>
      <div headerActions>
        @if (viewer.info(); as info) {
          <button type="button" class="btn-ghost text-xs" (click)="download(info.document_id)">Download</button>
        }
      </div>
      <div body class="doc-viewer-host__body">
        @if (viewer.config(); as cfg) {
          <app-universal-document-viewer [config]="cfg" />
        }
      </div>
    </app-modal>
  `,
  styles: [
    `
      .doc-viewer-host__icon {
        display: inline-flex;
        color: var(--text-muted, #666);
        margin-right: 0.5rem;
      }
      .doc-viewer-host__body {
        height: min(75vh, 720px);
      }
    `,
  ],
})
export class DocumentViewerHostComponent {
  readonly viewer = inject(DocumentViewerService);
  private readonly api = inject(DocumentPreviewApiService);

  readonly title = computed(
    () => this.viewer.info()?.file_name ?? this.viewer.config()?.fileName ?? 'Document',
  );
  readonly icon = computed(() => PREVIEW_TYPE_ICON[this.viewer.info()?.preview_type ?? 'unsupported']);

  download(documentId: string): void {
    this.api.downloadUrl(documentId).subscribe((url) => {
      window.open(url, '_blank', 'noopener');
    });
  }
}
