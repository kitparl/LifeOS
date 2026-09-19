import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { DocumentPreviewApiService } from './document-preview-api.service';

describe('DocumentPreviewApiService', () => {
  let service: DocumentPreviewApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(DocumentPreviewApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('fetches preview info without a retry flag by default', () => {
    service.getPreviewInfo('doc-1').subscribe();
    const req = http.expectOne((r) => r.url === `${environment.apiUrl}/files/doc-1/preview-info`);
    expect(req.request.params.has('retry')).toBe(false);
    req.flush({
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
  });

  it('passes retry=true when explicitly retrying', () => {
    service.getPreviewInfo('doc-1', { retry: true }).subscribe();
    const req = http.expectOne(
      (r) => r.url === `${environment.apiUrl}/files/doc-1/preview-info` && r.params.get('retry') === 'true',
    );
    expect(req.request.params.get('retry')).toBe('true');
    req.flush({});
  });

  it('mints a download token and builds a preview URL', () => {
    service.previewUrl('doc-1').subscribe((url) => {
      expect(url).toBe(`http://localhost:8000/api/v1/files/doc-1/preview?token=tok123`);
    });
    const req = http.expectOne(`${environment.apiUrl}/files/doc-1/download-token`);
    expect(req.request.method).toBe('POST');
    req.flush({ token: 'tok123', expires_at: new Date().toISOString() });
  });

  it('mints a download token and builds a download URL', () => {
    service.downloadUrl('doc-1').subscribe((url) => {
      expect(url).toBe(`http://localhost:8000/api/v1/files/doc-1/download?token=tok456`);
    });
    const req = http.expectOne(`${environment.apiUrl}/files/doc-1/download-token`);
    req.flush({ token: 'tok456', expires_at: new Date().toISOString() });
  });

  it('fetches raw text content', () => {
    service.fetchText('doc-1').subscribe((text) => expect(text).toBe('hello world'));
    const req = http.expectOne(`${environment.apiUrl}/files/doc-1/preview`);
    expect(req.request.method).toBe('GET');
    req.flush('hello world');
  });
});
