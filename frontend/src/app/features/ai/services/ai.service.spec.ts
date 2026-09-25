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

  it('should list use cases and assign a custom model', () => {
    service.listUseCases().subscribe((cases) => expect(cases.length).toBe(0));
    http.expectOne(`${environment.apiUrl}/ai/use-cases`).flush([]);

    service.setUseCaseModel('ai.rag_chat', { provider: 'openai', model: 'gpt-x', custom: true }).subscribe();
    const put = http.expectOne(`${environment.apiUrl}/ai/use-cases/ai.rag_chat/model`);
    expect(put.request.method).toBe('PUT');
    expect(put.request.body).toEqual({ provider: 'openai', model: 'gpt-x', custom: true });
    put.flush({});
  });

  it('should read and save AI settings', () => {
    const settings = { default_provider: null, timeout_seconds: 120, max_tokens: 1200, temperature: 0.3 };
    service.getSettings().subscribe((s) => expect(s.max_tokens).toBe(1200));
    http.expectOne(`${environment.apiUrl}/ai/settings`).flush(settings);

    service.saveSettings(settings).subscribe();
    const put = http.expectOne(`${environment.apiUrl}/ai/settings`);
    expect(put.request.method).toBe('PUT');
    put.flush(settings);
  });
});
