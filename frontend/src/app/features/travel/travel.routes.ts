import { Routes } from '@angular/router';
import { TravelShellComponent } from './travel-shell.component';

/** `/travel/*` — lazy chunk; Leaflet and all Travel code load only when a user opens Travel. */
export const TRAVEL_ROUTES: Routes = [
  {
    path: '',
    component: TravelShellComponent,
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'map' },
      { path: 'map', loadComponent: () => import('./pages/map-page.component').then((m) => m.MapPageComponent) },
      {
        path: 'wishlist',
        loadComponent: () => import('./pages/wishlist-page.component').then((m) => m.WishlistPageComponent),
      },
      { path: 'trips', loadComponent: () => import('./pages/trips-page.component').then((m) => m.TripsPageComponent) },
      {
        path: 'trips/:id',
        loadComponent: () => import('./pages/trip-detail.component').then((m) => m.TripDetailComponent),
      },
      {
        path: 'adventures',
        loadComponent: () => import('./pages/adventures-page.component').then((m) => m.AdventuresPageComponent),
      },
      {
        path: 'adventures/:id',
        loadComponent: () => import('./pages/adventure-detail.component').then((m) => m.AdventureDetailComponent),
      },
      {
        path: 'memories',
        loadComponent: () => import('./pages/memories-page.component').then((m) => m.MemoriesPageComponent),
      },
      {
        path: 'world',
        loadComponent: () => import('./pages/my-world-page.component').then((m) => m.MyWorldPageComponent),
      },
      {
        path: 'settings/usage',
        loadComponent: () => import('./pages/maps-usage-page.component').then((m) => m.MapsUsagePageComponent),
      },
      {
        path: 'places/:id',
        loadComponent: () => import('./pages/place-detail.component').then((m) => m.PlaceDetailComponent),
      },
    ],
  },
];
