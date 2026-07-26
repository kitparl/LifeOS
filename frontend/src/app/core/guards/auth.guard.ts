import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Waits for the bootstrap refresh to complete before deciding.
 * Prevents flash-logout on hard refresh or new tab open.
 */
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  // authReady is true after bootstrap() resolves — guaranteed by APP_INITIALIZER
  if (!auth.authReady()) {
    // Should not happen in normal flow, but guard against it
    return router.createUrlTree(['/login']);
  }

  if (auth.isAuthenticated()) {
    return true;
  }
  return router.createUrlTree(['/login']);
};

export const guestGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!auth.isAuthenticated()) {
    return true;
  }
  return router.createUrlTree(['/analytics/dashboard']);
};
