import { Routes } from '@angular/router';
import { dsaAdminGuard } from './guards/dsa-admin.guard';

/** DSA practice: patterns → problems → editor/judge; admin editing behind dsaAdminGuard (server-enforced). */
export const DSA_ROUTES: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () => import('./pages/dsa-overview.page').then((m) => m.DsaOverviewPageComponent),
  },
  {
    path: 'patterns/:slug',
    loadComponent: () => import('./pages/pattern-problems.page').then((m) => m.PatternProblemsPageComponent),
  },
  {
    path: 'problems/:slug',
    loadComponent: () => import('./pages/problem-detail.page').then((m) => m.ProblemDetailPageComponent),
  },
  {
    path: 'admin/problems/:slug',
    canActivate: [dsaAdminGuard],
    loadComponent: () => import('./pages/admin-problem-editor.page').then((m) => m.AdminProblemEditorPageComponent),
  },
];
