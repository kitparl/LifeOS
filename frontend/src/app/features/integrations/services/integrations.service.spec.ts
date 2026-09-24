import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { IntegrationsService } from './integrations.service';

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
