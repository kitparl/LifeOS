import { Injectable, signal } from '@angular/core';
import { DocumentViewerConfig, PreviewInfo } from './models/document-preview.model';

export interface DocumentViewerRef {
  close(): void;
}

/**
 * Opens the universal document viewer from anywhere in the app with one call:
 *
 *   this.documentViewerService.open({ documentId: doc.id });
 *
 * Mirrors ConfirmService's service+host pattern: this service only holds
 * state (signals); DocumentViewerHostComponent (mounted once in the app
 * shell) renders the actual <app-modal> reading that state. `info` is
 * written by UniversalDocumentViewerComponent once preview-info resolves,
 * so the host's header (icon, download) can react to it too.
 */
@Injectable({ providedIn: 'root' })
export class DocumentViewerService {
  readonly isOpen = signal(false);
  readonly config = signal<DocumentViewerConfig | null>(null);
  readonly info = signal<PreviewInfo | null>(null);

  open(config: DocumentViewerConfig): DocumentViewerRef {
    this.config.set(config);
    this.info.set(null);
    this.isOpen.set(true);
    return { close: () => this.close() };
  }

  close(): void {
    this.isOpen.set(false);
  }

  setInfo(info: PreviewInfo | null): void {
    this.info.set(info);
  }
}
