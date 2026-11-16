import { Component, Input, OnChanges } from '@angular/core';
import { MapLine, MapMarker, TravelMapComponent } from '../../travel/map/travel-map.component';

/** The route of a recorded run on the existing Leaflet map wrapper. */
@Component({
  selector: 'app-run-route-map',
  standalone: true,
  imports: [TravelMapComponent],
  host: { class: 'contents' },
  template: `
    @if (lines.length) {
      <div class="panel !p-0 overflow-hidden" data-testid="run-route-map">
        <div class="title-bar">Route</div>
        <div style="height: 18rem">
          <app-travel-map [lines]="lines" [markers]="markers" [autoFit]="true" ariaLabel="Run route map" />
        </div>
      </div>
    }
  `,
})
export class RunRouteMapComponent implements OnChanges {
  /** [latitude, longitude] pairs in running order. */
  @Input({ required: true }) route: [number, number][] = [];

  lines: MapLine[] = [];
  markers: MapMarker[] = [];

  ngOnChanges(): void {
    if (this.route.length < 2) {
      this.lines = [];
      this.markers = [];
      return;
    }
    const first = this.route[0];
    const last = this.route[this.route.length - 1];
    this.lines = [{ id: 'route', points: this.route, color: '--primary' }];
    this.markers = [
      { id: 'start', kind: 'start', label: 'Start', lat: first[0], lng: first[1], color: '--success' },
      { id: 'finish', kind: 'finish', label: 'Finish', lat: last[0], lng: last[1], color: '--danger' },
    ];
  }
}
