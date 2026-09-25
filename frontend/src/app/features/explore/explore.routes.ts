import { Routes } from '@angular/router';
import { exploreGuard } from './explore.guard';
import { EXPLORE_TOOLS } from './explore-tools.registry';

/** Public (no authGuard) route tree for free tools, rendered inside the guest shell. */
export const EXPLORE_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./guest-shell.component').then((m) => m.GuestShellComponent),
    canActivateChild: [exploreGuard],
    children: [
      {
        path: '',
        pathMatch: 'full',
        loadComponent: () => import('./explore-home.component').then((m) => m.ExploreHomeComponent),
      },
      ...EXPLORE_TOOLS.map((tool) => ({
        path: tool.path,
        providers: tool.providers,
        loadChildren: tool.loadChildren,
      })),
      { path: '**', redirectTo: '' },
    ],
  },
];
