import { Component, computed, input } from '@angular/core';
import { MapLine, MapMarker, TravelMapComponent } from '../../map/travel-map.component';
import { PlanDocument } from '../../models/share.models';
import { decodePolyline } from '../../utils/geo';
import { PlanFacts } from '../plan-route';

/** Same day colours as the list (as hex: Leaflet canvas can't read CSS variables). */
const DAY_HEX = ['#c2410c', '#0e7490', '#7c3aed', '#15803d', '#be185d', '#a16207', '#1d4ed8', '#4d7c0f'];

/** The plan on a map: numbered stops in day colours; each day's road route as a solid line once
 * known, else its order as a dashed line (from where the day starts). */
@Component({
  selector: 'app-planner-map',
  standalone: true,
  imports: [TravelMapComponent],
  template: `<app-travel-map class="map" [markers]="markers()" [lines]="lines()" [fitKey]="fitKey()" tileReferrerPolicy="strict-origin" ariaLabel="Map of the plan" />`,
  styles: [`:host { display: block; height: 100%; min-height: 18rem; } .map { display: block; height: 100%; border-radius: var(--tp-radius); overflow: hidden; }`],
})
export class PlannerMapComponent {
  readonly plan = input.required<PlanDocument>();
  readonly facts = input<PlanFacts | null>(null);

  readonly markers = computed<MapMarker[]>(() =>
    this.plan().days.flatMap((day, d) =>
      day.stops.flatMap((stop, i) =>
        stop.place
          ? [{ id: stop.id, kind: 'stop', lat: stop.place.lat, lng: stop.place.lng, label: `Day ${d + 1} · ${i + 1}. ${stop.title}`, color: DAY_HEX[d % DAY_HEX.length] }]
          : [],
      ),
    ),
  );

  readonly lines = computed<MapLine[]>(() =>
    this.plan().days.map((day, d) => {
      const facts = this.facts()?.days[d];
      const road = facts?.road ? day.route?.legs.flatMap((leg) => (leg.polyline ? decodePolyline(leg.polyline) : [])) : null;
      const points = road?.length ? road : facts?.chain.length ? facts.chain : day.stops.flatMap((s) => (s.place ? [[s.place.lat, s.place.lng] as [number, number]] : []));
      return { id: `day-${d}`, points, color: DAY_HEX[d % DAY_HEX.length], dashed: !road?.length };
    }),
  );

  /** Re-fit when places are added or removed, not on every text edit. */
  readonly fitKey = computed(() => this.markers().map((m) => m.id).join(','));
}
