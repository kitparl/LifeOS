import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AuthService } from './auth.service';
import { environment } from '../../../environments/environment';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    sessionStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
    expect(service.isAuthenticated()).toBeFalse();
  });

  it('login stores token and sets authenticated', () => {
    service.login({ identifier: 'a@b.com', password: 'password1' }).subscribe();

    const loginReq = httpMock.expectOne(`${environment.apiUrl}/auth/login`);
    expect(loginReq.request.method).toBe('POST');
    loginReq.flush({ access_token: 'test-token' });

    const meReq = httpMock.expectOne(`${environment.apiUrl}/auth/me`);
    meReq.flush({
      id: '1',
      email: 'a@b.com',
      display_name: 'Test',
      timezone: 'UTC',
    });

    expect(service.getToken()).toBe('test-token');
    expect(service.isAuthenticated()).toBeTrue();
  });

  it('googleLogin sends only the Google credential and sets authenticated', () => {
    service.googleLogin('google-id-token').subscribe();

    const req = httpMock.expectOne(`${environment.apiUrl}/auth/google`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ credential: 'google-id-token' });
    expect(req.request.withCredentials).toBeTrue();
    req.flush({ access_token: 'google-token' });

    httpMock.expectOne(`${environment.apiUrl}/auth/me`).flush({
      id: '1',
      email: 'a@b.com',
      display_name: 'Test',
      timezone: 'UTC',
    });

    expect(service.getToken()).toBe('google-token');
    expect(service.isAuthenticated()).toBeTrue();
  });

  it('googleLogin rejection keeps the user unauthenticated', () => {
    let detail: string | undefined;
    service.googleLogin('google-id-token').subscribe({
      error: (err) => (detail = err.error?.detail),
    });

    httpMock.expectOne(`${environment.apiUrl}/auth/google`).flush(
      { detail: 'User not found. Please contact your administrator to get access.' },
      { status: 401, statusText: 'Unauthorized' },
    );

    expect(detail).toBe('User not found. Please contact your administrator to get access.');
    expect(service.isAuthenticated()).toBeFalse();
  });
});
