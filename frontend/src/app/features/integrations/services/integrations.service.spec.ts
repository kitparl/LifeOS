import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { IntegrationsService, apiErrorMessage } from './integrations.service';

describe('IntegrationsService (Google Calendar)', () => {
  let service: IntegrationsService;
  let http: HttpTestingController;
  const api = `${environment.apiUrl}/integrations/google-calendar`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(IntegrationsService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('starts OAuth with the selected mode', () => {
    service.startGoogleCalendarOAuth('two_way').subscribe((r) => expect(r.auth_url).toBe('https://x'));
    const req = http.expectOne(`${api}/oauth/start?mode=two_way`);
    expect(req.request.method).toBe('GET');
    req.flush({ auth_url: 'https://x' });
  });

  it('posts the OAuth code and state to the callback', () => {
    service.completeGoogleCalendarOAuth('c', 's').subscribe();
    const req = http.expectOne(`${api}/oauth/callback`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ code: 'c', state: 's' });
    req.flush({});
  });

  it('saves config, syncs and disconnects', () => {
    service.saveGoogleCalendarConfig({ sync_direction: 'google_to_lifeos', enabled: true }).subscribe();
    const put = http.expectOne(`${api}/config`);
    expect(put.request.method).toBe('PUT');
    put.flush({});

    service.syncGoogleCalendar().subscribe();
    const sync = http.expectOne(`${api}/sync`);
    expect(sync.request.method).toBe('POST');
    sync.flush({ provider: 'google_calendar', status: 'synced', message: 'ok', synced_at: '' });

    service.disconnectGoogleCalendar().subscribe();
    const del = http.expectOne(api);
    expect(del.request.method).toBe('DELETE');
    del.flush(null);
  });
});

describe('IntegrationsService (AI providers)', () => {
  let service: IntegrationsService;
  let http: HttpTestingController;
  const api = `${environment.apiUrl}/integrations/ai`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(IntegrationsService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('reads and saves provider config', () => {
    service.getAiProvider('anthropic').subscribe((s) => expect(s.api_key_masked).toBe('****1234'));
    http.expectOne(`${api}/anthropic/config`).flush({ api_key_masked: '****1234' });

    service.saveAiProvider('anthropic', { api_key: 'k', default_model: 'm', custom_model: true }).subscribe();
    const put = http.expectOne(`${api}/anthropic/config`);
    expect(put.request.method).toBe('PUT');
    expect(put.request.body).toEqual({ api_key: 'k', default_model: 'm', custom_model: true });
    put.flush({});
  });

  it('tests, lists and refreshes models', () => {
    service.testAiProvider('gemini').subscribe((r) => expect(r.ok).toBeTrue());
    const test = http.expectOne(`${api}/gemini/test`);
    expect(test.request.method).toBe('POST');
    test.flush({ ok: true, detail: 'ok' });

    service.listAiModels('gemini').subscribe((r) => expect(r.models.length).toBe(1));
    http.expectOne(`${api}/gemini/models`).flush({ provider: 'gemini', models: [{ model_id: 'x' }], refreshed_at: null });

    service.refreshAiModels('gemini').subscribe();
    const refresh = http.expectOne(`${api}/gemini/models/refresh`);
    expect(refresh.request.method).toBe('POST');
    refresh.flush({ provider: 'gemini', models: [], refreshed_at: null });
  });
});

describe('IntegrationsService (AI model list)', () => {
  let service: IntegrationsService;
  let http: HttpTestingController;
  const api = `${environment.apiUrl}/integrations/ai/openrouter/models`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(IntegrationsService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('adds, removes and tests model ids in the request body (ids may contain "/")', () => {
    service.addAiModel('openrouter', 'meta-llama/llama-4:free').subscribe();
    const add = http.expectOne(api);
    expect(add.request.body).toEqual({ model_id: 'meta-llama/llama-4:free', capability: 'chat' });
    add.flush({ provider: 'openrouter', models: [], refreshed_at: null });

    service.removeAiModel('openrouter', 'meta-llama/llama-4:free').subscribe();
    const remove = http.expectOne(`${api}/remove`);
    expect(remove.request.body).toEqual({ model_id: 'meta-llama/llama-4:free' });
    remove.flush({ provider: 'openrouter', models: [], refreshed_at: null });

    service.testAiModel('openrouter', 'anthropic/claude-opus-5').subscribe((r) => expect(r.ok).toBeTrue());
    const test = http.expectOne(`${api}/test`);
    expect(test.request.method).toBe('POST');
    test.flush({ ok: true, detail: 'Model responded', model_id: 'anthropic/claude-opus-5' });
  });
});

describe('apiErrorMessage', () => {
  it('reads string, coded, and validation details', () => {
    expect(apiErrorMessage({ error: { detail: 'plain' } }, 'fb')).toBe('plain');
    expect(apiErrorMessage({ error: { detail: { code: 'x', message: 'coded' } } }, 'fb')).toBe('coded');
    expect(apiErrorMessage({ error: { detail: [{ msg: 'bad url' }] } }, 'fb')).toBe('bad url');
    expect(apiErrorMessage(null, 'fb')).toBe('fb');
  });
});
