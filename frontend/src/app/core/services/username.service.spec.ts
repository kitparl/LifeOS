import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../environments/environment';
import { UsernameService } from './username.service';

describe('UsernameService', () => {
  let service: UsernameService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(UsernameService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('checks availability', () => {
    let result: unknown;
    service.checkAvailability('john').subscribe((r) => (result = r));
    const req = http.expectOne(
      `${environment.apiUrl}/auth/username-available?username=john`,
    );
    expect(req.request.method).toBe('GET');
    req.flush({ username: 'john', available: true, reason: null });
    expect(result).toEqual({ username: 'john', available: true, reason: null });
  });

  it('changes username', () => {
    service.changeUsername({ username: 'newname', reason: 'test' }).subscribe();
    const req = http.expectOne(`${environment.apiUrl}/auth/me/username`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ username: 'newname', reason: 'test' });
    req.flush({
      id: '1',
      email: 'a@b.com',
      username: 'newname',
      display_name: 'A',
      timezone: 'UTC',
    });
  });
});
