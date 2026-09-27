import { Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { TabHubComponent, TabHubItem } from '../../shared/tab-hub/tab-hub.component';
import { MapsStatus } from './models/travel.models';
import { MapsApiService } from './services/maps-api.service';

const TABS: TabHubItem[] = [
  { id: 'map', label: 'Map' },
  { id: 'wishlist', label: 'Travel Wishlist' },
  { id: 'trips', label: 'Trips' },
  { id: 'adventures', label: 'Adventures' },
  { id: 'memories', label: 'Memories' },
  { id: 'world', label: 'My World' },
];

/** Travel section: tab bar + child pages inside the existing app shell (no new shell, spec §4/§34). */
@Component({
  selector: 'app-travel-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, TabHubComponent],
  template: `
    <div class="space-y-3">
      <app-tab-hub [tabs]="tabs" [activeId]="active()" [wrap]="true" (tabChange)="go($event)">
        <a routerLink="/travel/settings/usage" class="text-xs underline" title="Google Maps usage and cost protection">Maps usage</a>
      </app-tab-hub>
      @if (status(); as s) {
        @if (s.non_essential_blocked) {
          <p class="text-xs rounded p-2" style="background: var(--warning-soft)">
            ⚠️ Maps cost protection activated. New non-essential Google Maps requests are paused. Your saved travel data remains available.
            <a routerLink="/travel/settings/usage" class="underline">View usage</a>
          </p>
        } @else if (s.level === 'warning' || s.level === 'high' || s.level === 'critical') {
          <p class="text-xs rounded p-2" style="background: var(--warning-soft)">
            ⚠️ Google Maps usage is high this month.
            <a routerLink="/travel/settings/usage" class="underline">View usage</a>
          </p>
        }
      }
      <router-outlet />
    </div>
  `,
})
export class TravelShellComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly maps = inject(MapsApiService);
  private readonly destroyRef = inject(DestroyRef);

  readonly tabs = TABS;
  readonly active = signal('map');
  readonly status = signal<MapsStatus | null>(null);

  ngOnInit(): void {
    this.syncActive(this.router.url);
    this.router.events
      .pipe(
        filter((e): e is NavigationEnd => e instanceof NavigationEnd),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((e) => this.syncActive(e.urlAfterRedirects));
    this.maps.status().subscribe({ next: (s) => this.status.set(s), error: () => this.status.set(null) });
  }

  go(tab: string): void {
    void this.router.navigate(['/travel', tab]);
  }

  private syncActive(url: string): void {
    const segment = url.split('?')[0].split('/')[2] ?? 'map';
    const byRoute: Record<string, string> = { places: 'wishlist', settings: '' };
    this.active.set(byRoute[segment] ?? segment);
  }
}
