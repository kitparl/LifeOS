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
    service.login({ email: 'a@b.com', password: 'password1' }).subscribe();

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
});
