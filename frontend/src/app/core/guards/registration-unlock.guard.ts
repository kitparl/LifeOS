import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';
import { RegistrationGateService } from '../services/registration-gate.service';

export const registrationUnlockGuard: CanActivateFn = () => {
  const gate = inject(RegistrationGateService);
  const router = inject(Router);

  return gate.status().pipe(
    map((s) => (s.unlocked ? true : router.createUrlTree(['/register-access']))),
    catchError(() => of(router.createUrlTree(['/register-access']))),
  );
};
