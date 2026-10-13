import { Component, computed, input, output } from '@angular/core';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { MapLine, MapMarker, TravelMapComponent } from '../map/travel-map.component';
import { PlanDocument, VersionDetail } from '../models/share.models';
import { dayColor } from '../models/travel.models';
import { StopChange, compareDays } from '../utils/plan-summary';

const CHANGE_LABELS: Record<StopChange, string> = { added: 'Added', removed: 'Removed', changed: 'Changed', same: '' };

/** Read-only look at a version (map + days), or the same version compared with the Original. */
@Component({
  selector: 'app-share-version-preview',
  standalone: true,
  imports: [ModalComponent, TravelMapComponent],
  template: `
    <app-modal [open]="!!version()" [title]="title()" maxWidth="960px" [maximizable]="true" [hasFooter]="false" (closed)="closed.emit()">
      <div body class="space-y-3 text-sm">
        @if (version(); as v) {
          @if (!original()) {
            <div class="h-64 overflow-hidden rounded">
              <app-travel-map [markers]="markers()" [lines]="lines()" ariaLabel="Map of this version" />
            </div>
          }
          @for (day of days(); track day.day) {
            <section class="space-y-1">
              <h3 class="font-medium">
                <span [style.color]="'var(' + color(day.day) + ')'" aria-hidden="true">●</span>
                Day {{ day.day + 1 }}{{ dayTitle(day.day) }}
              </h3>
              @if (!day.stops.length) {
                <p class="text-xs" style="color: var(--text-muted)">Nothing planned.</p>
              }
              <ol class="space-y-1 pl-4">
                @for (row of day.stops; track row.stop.id + row.change) {
                  <li [class.line-through]="row.change === 'removed'" [attr.data-change]="row.change">
                    @if (original() && row.change !== 'same') {
                      <span class="chip mr-1 text-xs">{{ changeLabel(row.change) }}</span>
                    }
                    {{ row.stop.title }}
                    @if (row.stop.start_time) { <span class="text-xs">· {{ row.stop.start_time.slice(0, 5) }}</span> }
                    @if (row.stop.place && row.stop.place.name !== row.stop.title) {
                      <span class="text-xs" style="color: var(--text-muted)">· {{ row.stop.place.name }}</span>
                    }
                    @if (row.stop.stay) { <span class="text-xs">· stay: {{ row.stop.stay }}</span> }
                    @if (row.stop.notes) { <p class="text-xs" style="color: var(--text-muted)">{{ row.stop.notes }}</p> }
                  </li>
                }
              </ol>
            </section>
          }
        }
      </div>
    </app-modal>
  `,
})
export class ShareVersionPreviewComponent {
  readonly version = input<VersionDetail | null>(null);
  /** When set, the version is shown against this Original with Added / Removed / Changed labels. */
  readonly original = input<PlanDocument | null>(null);
  readonly closed = output<void>();

  readonly title = computed(() => {
    const v = this.version();
    return v ? (this.original() ? `${v.label} compared with the Original` : v.label) : '';
  });

  readonly days = computed(() => {
    const v = this.version();
    if (!v) return [];
    const base = this.original() ?? v.document;
    return compareDays(base, v.document);
  });

  readonly markers = computed<MapMarker[]>(() =>
    (this.version()?.document.days ?? []).flatMap((day, d) =>
      day.stops.flatMap((stop, i) =>
        stop.place
          ? [{ id: stop.id, kind: 'stop', lat: stop.place.lat, lng: stop.place.lng, label: `Day ${d + 1} · ${i + 1}. ${stop.title}`, color: dayColor(d) }]
          : [],
      ),
    ),
  );

  readonly lines = computed<MapLine[]>(() =>
    (this.version()?.document.days ?? []).map((day, d) => ({
      id: `day-${d}`,
      points: day.stops.flatMap((s) => (s.place ? [[s.place.lat, s.place.lng] as [number, number]] : [])),
      color: dayColor(d),
      dashed: true,
    })),
  );

  color(day: number): string {
    return dayColor(day);
  }

  dayTitle(day: number): string {
    const title = this.version()?.document.days[day]?.title;
    return title ? ` · ${title}` : '';
  }

  changeLabel(change: StopChange): string {
    return CHANGE_LABELS[change];
  }
}
