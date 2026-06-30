import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { AiService } from './ai.service';

describe('AiService', () => {
  let service: AiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should send chat message', () => {
    service.chat('Hello').subscribe((res) => expect(res.reply).toBe('Hi'));
    const req = http.expectOne(`${environment.apiUrl}/ai/chat`);
    expect(req.request.method).toBe('POST');
    req.flush({ reply: 'Hi', sources: [] });
  });
});
