import { ApplicationConfig, inject, isDevMode, provideZoneChangeDetection } from '@angular/core';
import { provideRouter, Router, withNavigationErrorHandler } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideServiceWorker } from '@angular/service-worker';

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { offlineInterceptor } from './core/interceptors/offline.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(
      routes,
      withNavigationErrorHandler((error) => {
        if (typeof navigator !== 'undefined' && !navigator.onLine) {
          void inject(Router).navigateByUrl('/offline');
          return;
        }
        throw error;
      }),
    ),
    provideHttpClient(withInterceptors([authInterceptor, offlineInterceptor])),
    provideServiceWorker('ngsw-worker.js', {
      enabled: !isDevMode(),
      registrationStrategy: 'registerWhenStable:30000',
    }),
  ],
};
