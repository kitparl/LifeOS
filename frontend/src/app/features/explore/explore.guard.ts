import { inject } from '@angular/core';
import { CanActivateChildFn, Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { toAuthenticatedUrl } from './explore-tools.registry';

/**
 * Explore Tools are public. Logged-in users are sent to the same tool inside the authenticated
 * app instead, so they always keep their full workspace (AI, notifications, etc.).
 */
export const exploreGuard: CanActivateChildFn = (_route, state) => {
  const auth = inject(AuthService);
  if (auth.isAuthenticated()) {
    return inject(Router).parseUrl(toAuthenticatedUrl(state.url));
  }
  return true;
};
