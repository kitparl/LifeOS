import { Provider, inject } from '@angular/core';
import { CanActivateFn, Router, Routes } from '@angular/router';
import { NEWS_ACCESS_MODE, newsRootPath } from './news-access-mode';

/** Collections are account data: guests deep-linking to one land on the (locked) Collections tab instead. */
export const newsAccountGuard: CanActivateFn = () => {
  const mode = inject(NEWS_ACCESS_MODE);
  if (mode === 'user') return true;
  return inject(Router).createUrlTree([newsRootPath(mode)], { queryParams: { tab: 'collections' } });
};

/**
 * News hub, article details, and collection pages. Mounted under `/news` (authenticated shell) and
 * under `/explore/news` (public guest shell), so links inside the feature stay relative or use
 * `newsRootPath()`.
 */
export const NEWS_ROUTES: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () => import('./news-hub.component').then((m) => m.NewsHubComponent),
  },
  {
    path: 'article',
    loadComponent: () => import('./pages/article-page.component').then((m) => m.NewsArticlePageComponent),
  },
  {
    path: 'collections/:id',
    canActivate: [newsAccountGuard],
    loadComponent: () =>
      import('./pages/collection-page.component').then((m) => m.NewsCollectionPageComponent),
  },
];

/** Route-level providers for the guest mount: browse live news; saving and collections are locked. */
export const NEWS_GUEST_PROVIDERS: Provider[] = [{ provide: NEWS_ACCESS_MODE, useValue: 'guest' }];
