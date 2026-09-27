import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';
import { DsaService } from '../services/dsa.service';

/** UI convenience only: the backend enforces is_admin on every admin route. */
export const dsaAdminGuard: CanActivateFn = () => {
  const router = inject(Router);
  const home = router.createUrlTree(['/dsa']);
  return inject(DsaService)
    .me()
    .pipe(
      map((me) => (me.can_edit ? true : home)),
      catchError(() => of(home)),
    );
};
