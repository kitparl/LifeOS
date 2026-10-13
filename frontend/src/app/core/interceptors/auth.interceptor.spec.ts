import { HttpClient, HttpContext, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { SKIP_LIFEOS_AUTH } from '../utils/http';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  let http: HttpClient;
  let controller: HttpTestingController;
  let auth: jasmine.SpyObj<AuthService>;

  beforeEach(() => {
    auth = jasmine.createSpyObj<AuthService>('AuthService', ['getToken', 'refresh']);
    auth.getToken.and.returnValue('lifeos-access');
    auth.refresh.and.returnValue(of('new-access'));
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: auth },
      ],
    });
    http = TestBed.inject(HttpClient);
    controller = TestBed.inject(HttpTestingController);
  });

  afterEach(() => controller.verify());

  it('adds the LifeOS Bearer token to normal requests', () => {
    http.get('/api/v1/tasks').subscribe();
    expect(controller.expectOne('/api/v1/tasks').request.headers.get('Authorization')).toBe('Bearer lifeos-access');
  });

  it('never sends the LifeOS session on shared-plan requests and never refreshes on their 401', () => {
    let status = 0;
    http
      .get('/api/v1/travel/shared/k7mq2p3x/me', { context: new HttpContext().set(SKIP_LIFEOS_AUTH, true) })
      .subscribe({ error: (err) => (status = err.status) });
    const req = controller.expectOne('/api/v1/travel/shared/k7mq2p3x/me');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({ detail: 'expired' }, { status: 401, statusText: 'Unauthorized' });
    expect(status).toBe(401);
    expect(auth.refresh).not.toHaveBeenCalled();
  });
});
