import { TestBed } from '@angular/core/testing';
import { DocumentViewerService } from './document-viewer.service';

describe('DocumentViewerService', () => {
  let service: DocumentViewerService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(DocumentViewerService);
  });

  it('starts closed with no config', () => {
    expect(service.isOpen()).toBe(false);
    expect(service.config()).toBeNull();
  });

  it('opens with just a documentId', () => {
    service.open({ documentId: 'doc-1' });
    expect(service.isOpen()).toBe(true);
    expect(service.config()).toEqual({ documentId: 'doc-1' });
  });

  it('opens with optional hints (fileName, mimeType)', () => {
    service.open({ documentId: 'doc-2', fileName: 'report.pdf', mimeType: 'application/pdf' });
    expect(service.config()).toEqual({
      documentId: 'doc-2',
      fileName: 'report.pdf',
      mimeType: 'application/pdf',
    });
  });

  it('resets info when a new document is opened', () => {
    service.open({ documentId: 'doc-1' });
    service.setInfo({
      document_id: 'doc-1',
      file_name: 'a.pdf',
      original_mime_type: 'application/pdf',
      preview_type: 'pdf',
      status: 'ready',
      preview_url: '/api/v1/files/doc-1/preview',
      download_url: '/api/v1/files/doc-1/download',
      page_count: null,
      error: null,
    });
    expect(service.info()).not.toBeNull();

    service.open({ documentId: 'doc-2' });
    expect(service.info()).toBeNull();
  });

  it('returns a ref whose close() closes the viewer', () => {
    const ref = service.open({ documentId: 'doc-1' });
    expect(service.isOpen()).toBe(true);
    ref.close();
    expect(service.isOpen()).toBe(false);
  });

  it('close() closes the viewer without clearing config', () => {
    service.open({ documentId: 'doc-1' });
    service.close();
    expect(service.isOpen()).toBe(false);
    expect(service.config()).toEqual({ documentId: 'doc-1' });
  });
});
