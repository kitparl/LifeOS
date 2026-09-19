import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { SimpleChange } from '@angular/core';
import { ComponentFixture, TestBed, fakeAsync, flush, tick } from '@angular/core/testing';
import { environment } from '../../../../../environments/environment';
import { UniversalDocumentViewerComponent } from './universal-document-viewer.component';

const infoBase = {
  file_name: 'file',
  original_mime_type: 'application/octet-stream',
  download_url: '/api/v1/files/doc-1/download',
  page_count: null,
  error: null,
};

describe('UniversalDocumentViewerComponent', () => {
  let fixture: ComponentFixture<UniversalDocumentViewerComponent>;
  let component: UniversalDocumentViewerComponent;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [UniversalDocumentViewerComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    fixture = TestBed.createComponent(UniversalDocumentViewerComponent);
    component = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function flushPreviewInfo(body: Record<string, unknown>): void {
    http.expectOne((r) => r.url === `${environment.apiUrl}/files/doc-1/preview-info`).flush(body);
  }

  it('goes straight to ready for a native PDF (no conversion needed)', fakeAsync(() => {
    component.config = { documentId: 'doc-1' };
    component.ngOnChanges({ config: new SimpleChange(null, component.config, true) });

    flushPreviewInfo({
      ...infoBase,
      document_id: 'doc-1',
      preview_type: 'pdf',
      status: 'ready',
      preview_url: '/api/v1/files/doc-1/preview',
    });
    http.expectOne(`${environment.apiUrl}/files/doc-1/download-token`).flush({
      token: 'tok',
      expires_at: new Date().toISOString(),
    });
    tick();

    expect(component.state()).toBe('ready');
    expect(component.previewType()).toBe('pdf');
    flush();
  }));

  it('shows unsupported without ever requesting a preview URL', fakeAsync(() => {
    component.config = { documentId: 'doc-1' };
    component.ngOnChanges({ config: new SimpleChange(null, component.config, true) });

    flushPreviewInfo({
      ...infoBase,
      document_id: 'doc-1',
      preview_type: 'unsupported',
      status: 'ready',
      preview_url: null,
    });
    tick();

    expect(component.state()).toBe('unsupported');
    flush();
  }));

  it('polls while processing, then resolves to ready', fakeAsync(() => {
    component.config = { documentId: 'doc-1' };
    component.ngOnChanges({ config: new SimpleChange(null, component.config, true) });

    flushPreviewInfo({
      ...infoBase,
      document_id: 'doc-1',
      preview_type: 'pdf',
      status: 'processing',
      preview_url: null,
    });
    expect(component.state()).toBe('processing');

    tick(1000); // first poll backoff
    flushPreviewInfo({
      ...infoBase,
      document_id: 'doc-1',
      preview_type: 'pdf',
      status: 'ready',
      preview_url: '/api/v1/files/doc-1/preview',
    });
    http.expectOne(`${environment.apiUrl}/files/doc-1/download-token`).flush({
      token: 'tok',
      expires_at: new Date().toISOString(),
    });
    tick();

    expect(component.state()).toBe('ready');
    flush();
  }));

  it('surfaces a stable failed state with a Retry action', fakeAsync(() => {
    component.config = { documentId: 'doc-1' };
    component.ngOnChanges({ config: new SimpleChange(null, component.config, true) });

    flushPreviewInfo({
      ...infoBase,
      document_id: 'doc-1',
      preview_type: 'pdf',
      status: 'failed',
      preview_url: null,
      error: 'Document conversion failed',
    });
    tick();

    expect(component.state()).toBe('failed');
    expect(component.errorMessage()).toBe('Document conversion failed');

    component.retry();
    http
      .expectOne((r) => r.url === `${environment.apiUrl}/files/doc-1/preview-info` && r.params.get('retry') === 'true')
      .flush({ ...infoBase, document_id: 'doc-1', preview_type: 'pdf', status: 'processing', preview_url: null });
    expect(component.state()).toBe('processing');
    // A new poll is now scheduled — destroying the component (as the real
    // host does on close) cancels it, rather than letting it fire an
    // unflushed HTTP request when fakeAsync's flush() drains pending timers.
    fixture.destroy();
  }));

  it('renders text/csv/markdown types without minting a preview token', fakeAsync(() => {
    component.config = { documentId: 'doc-1' };
    component.ngOnChanges({ config: new SimpleChange(null, component.config, true) });

    flushPreviewInfo({
      ...infoBase,
      document_id: 'doc-1',
      preview_type: 'markdown',
      status: 'ready',
      preview_url: '/api/v1/files/doc-1/preview',
    });
    tick();

    expect(component.state()).toBe('ready');
    http.expectNone(`${environment.apiUrl}/files/doc-1/download-token`);
    flush();
  }));
});
