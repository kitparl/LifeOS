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

  it('should create vocabulary', () => {
    service.createVocabulary({ word: 'test', meaning: 'a test' }).subscribe((w) => expect(w.word).toBe('test'));
    const req = http.expectOne(`${environment.apiUrl}/communication/vocabulary`);
    req.flush({
      id: '1',
      word: 'test',
      meaning: 'a test',
      examples: null,
      pronunciation: null,
      synonyms: null,
      mastery: 1,
      notes: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  });
});
