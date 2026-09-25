import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree, provideRouter } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { exploreGuard } from './explore.guard';

describe('exploreGuard', () => {
  let authenticated: boolean;

  beforeEach(() => {
    authenticated = false;
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: { isAuthenticated: () => authenticated } },
      ],
    });
  });

  function run(url: string): ReturnType<typeof exploreGuard> {
    return TestBed.runInInjectionContext(() =>
      exploreGuard({} as ActivatedRouteSnapshot, { url } as RouterStateSnapshot),
    );
  }

  it('lets logged-out visitors through', () => {
    expect(run('/explore/developer/base64')).toBe(true);
  });

  it('redirects logged-in users to the same tool in the app', () => {
    authenticated = true;
    const result = run('/explore/developer/base64?mode=decode');
    expect(result instanceof UrlTree).toBe(true);
    expect(TestBed.inject(Router).serializeUrl(result as UrlTree)).toBe('/developer/base64?mode=decode');
  });

  it('redirects logged-in users on the Explore home to the app home', () => {
    authenticated = true;
    const result = run('/explore');
    expect(TestBed.inject(Router).serializeUrl(result as UrlTree)).toBe('/');
  });
});
