import { Routes } from '@angular/router';

/**
 * Split bills home. Mounted under `/splits` (authenticated shell) and `/explore/splits`
 * (guest shell). The group page itself is the public top-level `/s/:code`.
 */
export const SPLITS_ROUTES: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () => import('./pages/splits-home.component').then((m) => m.SplitsHomeComponent),
  },
];
