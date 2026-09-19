import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { CommunicationService } from './communication.service';

describe('CommunicationService', () => {
  let service: CommunicationService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(CommunicationService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should create writing practice', () => {
    service.createWriting({ title: 'test', content: 'a test' }).subscribe((w) => expect(w.title).toBe('test'));
    const req = http.expectOne(`${environment.apiUrl}/communication/writing`);
    req.flush({
      id: '1',
      title: 'test',
      content: 'a test',
      category: 'notes',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  });
});
