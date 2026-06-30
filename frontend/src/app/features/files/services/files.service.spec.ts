import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { FilesService } from './files.service';

describe('FilesService', () => {
  let service: FilesService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(FilesService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should upload a file', () => {
    const file = new File(['hello'], 'test.txt', { type: 'text/plain' });
    service.upload(file, 'wishlist').subscribe((r) => expect(r.filename).toBe('test.txt'));
    const req = http.expectOne(`${environment.apiUrl}/files/upload`);
    expect(req.request.method).toBe('POST');
    req.flush({
      id: '1',
      filename: 'test.txt',
      content_type: 'text/plain',
      size_bytes: 5,
      storage_backend: 'local',
      url: '/api/v1/files/1/content',
      module: 'wishlist',
      entity_id: null,
      created_at: new Date().toISOString(),
    });
  });
});
