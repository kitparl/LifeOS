import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree, provideRouter } from '@angular/router';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { dsaAdminGuard } from './dsa-admin.guard';

describe('dsaAdminGuard', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])] });
    http = TestBed.inject(HttpTestingController);
  });

  const run = (): Observable<boolean | UrlTree> =>
    TestBed.runInInjectionContext(
      () => dsaAdminGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot) as Observable<boolean | UrlTree>,
    );

  it('allows admins', () => {
    let result: boolean | UrlTree | undefined;
    run().subscribe((r) => (result = r));
    http.expectOne(`${environment.apiUrl}/dsa/me`).flush({ can_edit: true });
    expect(result).toBeTrue();
  });

  it('redirects everyone else to /dsa', () => {
    let result: boolean | UrlTree | undefined;
    run().subscribe((r) => (result = r));
    http.expectOne(`${environment.apiUrl}/dsa/me`).flush({ can_edit: false });
    expect(TestBed.inject(Router).serializeUrl(result as UrlTree)).toBe('/dsa');
  });
});
