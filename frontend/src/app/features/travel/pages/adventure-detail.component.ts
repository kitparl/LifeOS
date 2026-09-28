import { DatePipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { EMPTY, Observable, Subject, catchError, concatMap } from 'rxjs';
import { apiErrorMessage } from '../../../core/utils/http';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { RouteDraw } from '../map/route-draw';
import { LatLng, MapLine, MapMarker, TravelMapComponent } from '../map/travel-map.component';
import {
  ADVENTURE_KINDS,
  AdventureDetail,
  AdventureUpdate,
  AdventureWaypoint,
  DIFFICULTIES,
  GpxPreview,
  TripListItem,
  WAYPOINT_KINDS,
  WaypointKind,
  formatDistance,
} from '../models/travel.models';
import { TravelApiService } from '../services/travel-api.service';
import { pathLengthM } from '../utils/geo';

type Mode = 'select' | 'pin' | 'draw' | 'gpx';

const SOURCE_LABELS: Record<string, string> = {
  user_drawn: 'Drawn by you',
  gpx: 'Imported GPX',
  google: 'Google route',
  straight_line: 'Straight-line estimate',
};

/**
 * One adventure/trek: details, waypoints and its route (spec §14–§16). The map mode bar switches
 * between selecting, dropping waypoints, drawing a route (undo/redo) and importing a GPX file.
 */
@Component({
  selector: 'app-travel-adventure-detail',
  standalone: true,
  imports: [FormsModule, RouterLink, DatePipe, TravelMapComponent],
  template: `
    @if (detail(); as d) {
      <div class="space-y-3">
        <div class="panel grid gap-2 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <input class="input-field font-semibold sm:col-span-2" maxlength="200" aria-label="Adventure name" [ngModel]="d.adventure.name" (change)="save({ name: val($event) })" />
          <select class="input-field" aria-label="Type" [ngModel]="d.adventure.kind" (ngModelChange)="save({ kind: $event })">
            @for (k of kinds; track k.id) {
              <option [value]="k.id">{{ k.label }}</option>
            }
          </select>
          <select class="input-field capitalize" aria-label="Difficulty" [ngModel]="d.adventure.difficulty ?? ''" (ngModelChange)="save({ difficulty: $event || null })">
            <option value="">Difficulty…</option>
            @for (x of difficulties; track x) {
              <option [value]="x">{{ x }}</option>
            }
          </select>
          <label class="text-xs">Start <input class="input-field" type="date" [ngModel]="d.adventure.start_date" (change)="save({ start_date: val($event) || null })" /></label>
          <label class="text-xs">End <input class="input-field" type="date" [ngModel]="d.adventure.end_date" (change)="save({ end_date: val($event) || null })" /></label>
          <label class="text-xs sm:col-span-2">Trip
            <select class="input-field" [ngModel]="d.adventure.trip_id ?? ''" (ngModelChange)="save({ trip_id: $event || null })">
              <option value="">Not part of a trip</option>
              @for (t of trips(); track t.id) {
                <option [value]="t.id">{{ t.name }}</option>
              }
            </select>
          </label>
          <textarea class="input-field sm:col-span-2 lg:col-span-4" rows="2" placeholder="Notes" aria-label="Notes" [ngModel]="d.adventure.notes ?? ''" (change)="save({ notes: val($event) || null })"></textarea>
        </div>

        <div class="flex flex-wrap items-center gap-1" role="toolbar" aria-label="Map mode">
          @for (m of modes; track m.id) {
            <button type="button" class="text-xs" [class.btn-primary]="mode() === m.id" [class.btn-secondary]="mode() !== m.id" (click)="setMode(m.id)">{{ m.label }}</button>
          }
          <span class="ml-2 text-xs" style="color: var(--text-muted)">{{ hint() }}</span>
        </div>

        @if (mode() === 'draw') {
          <div class="panel flex flex-wrap items-center gap-2 text-xs">
            <span>{{ drawCount() }} points · {{ drawDistance() }}</span>
            <button type="button" class="btn-secondary text-xs" [disabled]="!draw.canUndo" (click)="undo()">Undo</button>
            <button type="button" class="btn-secondary text-xs" [disabled]="!draw.canRedo" (click)="redo()">Redo</button>
            <button type="button" class="btn-secondary text-xs" [disabled]="!drawCount()" (click)="removeLastPoint()">Remove last point</button>
            <input class="input-field !w-48 text-xs" maxlength="200" placeholder="Route name" aria-label="Route name" [(ngModel)]="routeName" />
            <button type="button" class="btn-primary text-xs" [disabled]="drawCount() < 2 || !routeName.trim() || busy()" (click)="finishDrawing()">Finish &amp; save</button>
          </div>
        }
        @if (mode() === 'gpx') {
          <div class="panel space-y-2 text-xs">
            <input type="file" accept=".gpx,application/gpx+xml,application/xml,text/xml" aria-label="GPX file" (change)="pickGpx($event)" />
            @if (gpx(); as g) {
              <p>
                {{ g.point_count }} points · {{ distance(g.distance_m) }}
                @if (g.elevation_gain_m !== null) { · ↑ {{ g.elevation_gain_m }} m ↓ {{ g.elevation_loss_m }} m }
                @if (g.start_time) { · {{ g.start_time | date: 'medium' }} }
                · {{ g.waypoints.length }} waypoints
              </p>
              <div class="flex flex-wrap items-center gap-2">
                <input class="input-field !w-56 text-xs" maxlength="200" placeholder="Route name" aria-label="GPX route name" [(ngModel)]="routeName" />
                <button type="button" class="btn-primary text-xs" [disabled]="!routeName.trim() || busy()" (click)="saveGpx()">Save to this adventure</button>
              </div>
            }
          </div>
        }

        <div class="grid gap-3 lg:grid-cols-[2fr_1fr]">
          <app-travel-map class="h-[55vh]" [markers]="markers()" [lines]="lines()" [fitKey]="fitKey()" [toolActive]="mode() === 'pin' || mode() === 'draw'" (mapTap)="onTap($event)" />
          <div class="space-y-3">
            <div class="panel space-y-1 text-sm">
              <p class="font-medium">Route</p>
              @if (d.route; as r) {
                <p class="text-xs">{{ r.name }} · {{ sourceLabel(r.source) }}</p>
                <p class="text-xs">{{ distance(r.distance_m) }}
                  @if (r.elevation_gain_m !== null) { · ↑ {{ r.elevation_gain_m }} m ↓ {{ r.elevation_loss_m }} m }
                </p>
                <div class="flex flex-wrap gap-2">
                  @if (r.elevation_gain_m === null) {
                    <button type="button" class="btn-secondary text-xs" [disabled]="busy()" (click)="elevation(r.id)">Get elevation</button>
                  }
                  @if (r.source === 'user_drawn' || r.source === 'gpx') {
                    <button type="button" class="btn-secondary text-xs" (click)="exportGpx(r.id, r.name)">Export GPX</button>
                  }
                </div>
              } @else {
                <p class="text-xs" style="color: var(--text-muted)">No route yet — use Draw Route or Import GPX.</p>
              }
            </div>
            <div class="panel space-y-2 text-sm">
              <p class="font-medium">Waypoints</p>
              @for (w of d.waypoints; track $index) {
                <div class="flex items-center gap-1">
                  <input class="input-field flex-1 text-xs" maxlength="200" [attr.aria-label]="'Waypoint ' + ($index + 1)" [ngModel]="w.name" (change)="renameWaypoint($index, val($event))" />
                  <select class="input-field !w-auto text-xs capitalize" aria-label="Waypoint type" [ngModel]="w.kind" (ngModelChange)="retypeWaypoint($index, $event)">
                    @for (k of waypointKinds; track k) {
                      <option [value]="k">{{ k }}</option>
                    }
                  </select>
                  <button type="button" class="text-xs" style="color: var(--danger)" aria-label="Remove waypoint" (click)="removeWaypoint($index)">✕</button>
                </div>
              } @empty {
                <p class="text-xs" style="color: var(--text-muted)">Use Drop Pin to add camps, summits, water points…</p>
              }
            </div>
            <div class="flex gap-2">
              <button type="button" class="text-xs" style="color: var(--danger)" (click)="remove()">Delete adventure</button>
              <a routerLink="/travel/trips" class="text-xs underline">All trips &amp; adventures</a>
            </div>
          </div>
        </div>
        @if (error()) {
          <p class="text-xs" style="color: var(--danger)">{{ error() }}</p>
        }
      </div>
    } @else if (notFound()) {
      <p class="text-sm">This adventure does not exist. <a routerLink="/travel/trips" class="underline">All trips &amp; adventures</a></p>
    } @else {
      <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
    }
  `,
})
export class AdventureDetailComponent implements OnInit {
  private readonly api = inject(TravelApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly confirm = inject(ConfirmService);

  readonly kinds = ADVENTURE_KINDS;
  readonly difficulties = DIFFICULTIES;
  readonly waypointKinds = WAYPOINT_KINDS;
  readonly modes: { id: Mode; label: string }[] = [
    { id: 'select', label: 'Select' },
    { id: 'pin', label: 'Drop Pin' },
    { id: 'draw', label: 'Draw Route' },
    { id: 'gpx', label: 'Import GPX' },
  ];
  readonly detail = signal<AdventureDetail | null>(null);
  readonly trips = signal<TripListItem[]>([]);
  readonly mode = signal<Mode>('select');
  readonly gpx = signal<GpxPreview | null>(null);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly notFound = signal(false);
  readonly draw = new RouteDraw();
  /** Bumped on every draw edit so computed signals re-read the (plain-class) draw state. */
  private readonly drawVersion = signal(0);
  private gpxFile: File | null = null;
  /** Full-list saves run one at a time, in order, so an older save can never land last. */
  private readonly waypointSaves = new Subject<{ id: string; waypoints: AdventureWaypoint[] }>();
  private pendingWaypointSaves = 0;
  routeName = '';

  readonly drawCount = computed(() => (this.drawVersion(), this.draw.points.length));
  readonly drawDistance = computed(() => (this.drawVersion(), formatDistance(pathLengthM(this.draw.points))));
  /** Bring a GPX preview, or a newly saved route, into view. */
  readonly fitKey = computed(() => {
    const g = this.gpx();
    if (this.mode() === 'gpx' && g) return `preview:${g.point_count}:${g.distance_m}`;
    return this.detail()?.route?.id ?? null;
  });

  readonly hint = computed(() => {
    switch (this.mode()) {
      case 'pin':
        return 'Tap the map to add a waypoint.';
      case 'draw':
        return 'Tap the map to add route points.';
      case 'gpx':
        return 'Choose a .gpx file to preview it on the map.';
      default:
        return '';
    }
  });

  readonly markers = computed<MapMarker[]>(() => {
    this.drawVersion();
    const d = this.detail();
    const waypoints = (d?.waypoints ?? []).map((w, i) => ({
      id: `wp-${i}`,
      kind: 'waypoint',
      lat: w.lat,
      lng: w.lng,
      label: w.name,
      color: w.kind === 'summit' ? '--danger' : w.kind === 'camp' ? '--success' : '--accent',
    }));
    const drawing = this.mode() === 'draw'
      ? this.draw.points.map(([lat, lng], i) => ({ id: `draw-${i}`, kind: 'draw', lat, lng, label: `Point ${i + 1}`, color: '--primary', radius: 4 }))
      : [];
    return [...waypoints, ...drawing];
  });

  readonly lines = computed<MapLine[]>(() => {
    this.drawVersion();
    const d = this.detail();
    const out: MapLine[] = [];
    if (d?.route_points.length) out.push({ id: 'route', points: d.route_points, color: d.route?.source === 'user_drawn' ? '--accent' : '--primary' });
    if (this.mode() === 'draw' && this.draw.points.length > 1) out.push({ id: 'drawing', points: [...this.draw.points], color: '--accent', dashed: true });
    const g = this.gpx();
    if (this.mode() === 'gpx' && g) out.push({ id: 'gpx', points: g.points, color: '--info', dashed: true });
    return out;
  });

  constructor() {
    this.waypointSaves
      .pipe(
        concatMap(({ id, waypoints }) =>
          this.api.setWaypoints(id, waypoints).pipe(
            catchError((err) => {
              this.pendingWaypointSaves--;
              this.fail(err);
              return EMPTY;
            }),
          ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((d) => {
        // Only the last queued save's response reflects everything the user did.
        if (--this.pendingWaypointSaves === 0) this.detail.set(d);
      });
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.api.getAdventure(id).subscribe({ next: (d) => this.detail.set(d), error: () => this.notFound.set(true) });
    this.api.listTrips({ limit: 100 }).subscribe({ next: (page) => this.trips.set(page.items) });
  }

  val(event: Event): string {
    return (event.target as HTMLInputElement).value.trim();
  }

  sourceLabel(source: string): string {
    return SOURCE_LABELS[source] ?? source;
  }

  distance(m: number): string {
    return formatDistance(m);
  }

  setMode(mode: Mode): void {
    this.mode.set(mode);
    this.error.set(null);
    if (mode === 'draw') {
      this.draw.reset();
      this.routeName = this.detail()?.adventure.name ?? '';
      this.drawVersion.update((v) => v + 1);
    }
    if (mode !== 'gpx') this.gpx.set(null);
  }

  undo(): void {
    this.drawOp(() => this.draw.undo());
  }

  redo(): void {
    this.drawOp(() => this.draw.redo());
  }

  removeLastPoint(): void {
    this.drawOp(() => this.draw.removeLast());
  }

  private drawOp(op: () => void): void {
    op();
    this.drawVersion.update((v) => v + 1);
  }

  onTap(point: LatLng): void {
    if (this.mode() === 'draw') {
      this.drawOp(() => this.draw.add([point.lat, point.lng]));
    } else if (this.mode() === 'pin') {
      const d = this.detail();
      if (!d) return;
      const waypoint: AdventureWaypoint = { lat: point.lat, lng: point.lng, name: `Waypoint ${d.waypoints.length + 1}`, kind: 'other', elevation_m: null };
      this.putWaypoints([...d.waypoints, waypoint]);
    }
  }

  renameWaypoint(index: number, name: string): void {
    const d = this.detail();
    if (!d || !name) return;
    this.putWaypoints(d.waypoints.map((w, i) => (i === index ? { ...w, name } : w)));
  }

  retypeWaypoint(index: number, kind: WaypointKind): void {
    const d = this.detail();
    if (d) this.putWaypoints(d.waypoints.map((w, i) => (i === index ? { ...w, kind } : w)));
  }

  removeWaypoint(index: number): void {
    const d = this.detail();
    if (d) this.putWaypoints(d.waypoints.filter((_, i) => i !== index));
  }

  save(patch: AdventureUpdate): void {
    const d = this.detail();
    if (!d || patch.name === '') return;
    this.run(this.api.updateAdventure(d.adventure.id, patch));
  }

  finishDrawing(): void {
    const d = this.detail();
    if (!d) return;
    this.busy.set(true);
    this.api
      .saveDrawnRoute({ name: this.routeName.trim(), mode: 'walking', points: [...this.draw.points], adventure_id: d.adventure.id })
      .subscribe({
        next: () => {
          this.setMode('select');
          this.reload();
        },
        error: (err) => this.fail(err),
      });
  }

  pickGpx(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    this.gpxFile = file;
    this.busy.set(true);
    this.error.set(null);
    this.api.previewGpx(file).subscribe({
      next: (preview) => {
        this.busy.set(false);
        this.gpx.set(preview);
        this.routeName = preview.name ?? file.name.replace(/\.gpx$/i, '');
      },
      error: (err) => this.fail(err),
    });
  }

  saveGpx(): void {
    const d = this.detail();
    if (!d || !this.gpxFile) return;
    this.busy.set(true);
    this.api.importGpx(this.gpxFile, this.routeName.trim(), { adventure_id: d.adventure.id, trip_id: d.adventure.trip_id }).subscribe({
      next: () => {
        this.gpxFile = null;
        this.setMode('select');
        this.reload();
      },
      error: (err) => this.fail(err),
    });
  }

  elevation(routeId: string): void {
    this.busy.set(true);
    this.api.fillElevation(routeId).subscribe({ next: () => this.reload(), error: (err) => this.fail(err) });
  }

  exportGpx(routeId: string, name: string): void {
    this.api.exportGpx(routeId).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${name}.gpx`;
        link.click();
        URL.revokeObjectURL(url);
      },
      error: (err) => this.fail(err),
    });
  }

  async remove(): Promise<void> {
    const d = this.detail();
    if (!d || !(await this.confirm.confirm('Its drawn and imported routes are deleted too.', `Delete ${d.adventure.name}?`))) return;
    this.api.deleteAdventure(d.adventure.id).subscribe({ next: () => void this.router.navigate(['/travel/trips']) });
  }

  /**
   * Waypoints are saved as a full list, so apply the edit locally first: a quick rename followed
   * by a type change must build on the rename, not on the list from before it.
   */
  private putWaypoints(waypoints: AdventureWaypoint[]): void {
    const d = this.detail();
    if (!d) return;
    this.detail.set({ ...d, waypoints });
    this.pendingWaypointSaves++;
    this.waypointSaves.next({ id: d.adventure.id, waypoints });
  }

  private reload(): void {
    const d = this.detail();
    if (d) this.run(this.api.getAdventure(d.adventure.id));
  }

  private run(request: Observable<AdventureDetail>): void {
    this.busy.set(true);
    this.error.set(null);
    request.subscribe({
      next: (d) => {
        this.detail.set(d);
        this.busy.set(false);
      },
      error: (err) => this.fail(err),
    });
  }

  private fail(err: unknown): void {
    this.busy.set(false);
    this.error.set(apiErrorMessage(err, 'Something went wrong'));
  }
}
