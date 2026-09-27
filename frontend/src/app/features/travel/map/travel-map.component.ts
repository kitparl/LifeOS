import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
  effect,
  input,
  output,
  signal,
} from '@angular/core';
import type * as Leaflet from 'leaflet';
import { environment } from '../../../../environments/environment';
import { loadLeaflet } from './leaflet-loader';

export interface LatLng {
  lat: number;
  lng: number;
}

export interface MapMarker extends LatLng {
  id: string;
  kind: string;
  label: string;
  /** CSS custom property name (e.g. `--success`) or a literal colour. */
  color: string;
  radius?: number;
}

export interface MapLine {
  id: string;
  points: [number, number][];
  color: string;
  /** Drafts and straight-line fallbacks are dashed. */
  dashed?: boolean;
}

const DEFAULT_CENTER: LatLng = { lat: 22.5, lng: 79 };
const DEFAULT_ZOOM = 4;

/**
 * The single Leaflet wrapper reused by every Travel tab.
 * It never calls an API: panning/zooming only moves tiles (spec §31). Taps and long-presses are
 * emitted for the page to decide what to do (drop a pin, add a route point, …).
 */
@Component({
  selector: 'app-travel-map',
  standalone: true,
  template: `
    <div #host class="travel-map h-full w-full" [attr.aria-label]="ariaLabel()" role="application"></div>
    @if (failed()) {
      <p class="p-3 text-xs" style="color: var(--danger)">The map could not be loaded. Your saved places are still in the lists.</p>
    }
  `,
  styles: [
    `:host { display: block; position: relative; min-height: 16rem; }
     .travel-map { min-height: inherit; border: 1px solid var(--border); border-radius: var(--radius-md); z-index: 0; }`,
  ],
})
export class TravelMapComponent implements AfterViewInit, OnDestroy {
  @ViewChild('host', { static: true }) private readonly host!: ElementRef<HTMLDivElement>;

  readonly markers = input<readonly MapMarker[]>([]);
  readonly lines = input<readonly MapLine[]>([]);
  readonly pin = input<LatLng | null>(null);
  /** Fit the view to the first markers/lines that arrive, unless the user has already moved the map. */
  readonly autoFit = input(true);
  readonly ariaLabel = input('Travel map');
  /**
   * Changing this key re-fits the view to everything drawn, even after the user moved the map —
   * for moments like "a GPX was just imported" where the new line must come into view.
   */
  readonly fitKey = input<string | null>(null);
  /** Crosshair cursor while a tool (drop pin, draw route) is active. */
  readonly toolActive = input(false);

  readonly mapTap = output<LatLng>();
  readonly markerSelect = output<MapMarker>();

  readonly failed = signal(false);
  private readonly ready = signal(false);

  private L: typeof Leaflet | null = null;
  private map: Leaflet.Map | null = null;
  private markerLayer: Leaflet.LayerGroup | null = null;
  private lineLayer: Leaflet.LayerGroup | null = null;
  private pinLayer: Leaflet.LayerGroup | null = null;
  private fitted = false;
  private movingProgrammatically = false;
  private lastFitKey: string | null = null;

  constructor() {
    effect(() => {
      const markers = this.markers();
      const lines = this.lines();
      const fitKey = this.fitKey();
      if (!this.ready()) return;
      this.render(markers, lines);
      if (fitKey && fitKey !== this.lastFitKey) {
        this.lastFitKey = fitKey;
        this.fitTo(markers, lines, 14);
        this.fitted = true;
      }
    });
    effect(() => {
      const pin = this.pin();
      if (this.ready()) this.renderPin(pin);
    });
    effect(() => {
      const active = this.toolActive();
      if (this.ready()) this.host.nativeElement.style.cursor = active ? 'crosshair' : '';
    });
  }

  async ngAfterViewInit(): Promise<void> {
    try {
      const L = await loadLeaflet();
      this.L = L;
      const map = L.map(this.host.nativeElement, { preferCanvas: true, worldCopyJump: true }).setView(
        [DEFAULT_CENTER.lat, DEFAULT_CENTER.lng],
        DEFAULT_ZOOM,
      );
      L.tileLayer(environment.travel.tileUrl, {
        attribution: environment.travel.tileAttribution,
        maxZoom: 19,
      }).addTo(map);
      this.lineLayer = L.layerGroup().addTo(map);
      this.markerLayer = L.layerGroup().addTo(map);
      this.pinLayer = L.layerGroup().addTo(map);
      const emitTap = (e: Leaflet.LeafletMouseEvent) =>
        this.mapTap.emit({ lat: round5(e.latlng.lat), lng: round5(wrapLng(e.latlng.lng)) });
      map.on('click', emitTap);
      // Leaflet reports a touch long-press as `contextmenu` (spec §33: long press drops a pin too).
      map.on('contextmenu', emitTap);
      // Once the user taps, drags or zooms, the view is theirs: never auto-fit over it.
      map.on('click contextmenu dragstart', () => (this.fitted = true));
      map.on('zoomstart', () => {
        if (!this.movingProgrammatically) this.fitted = true;
      });
      this.map = map;
      this.ready.set(true);
    } catch {
      this.failed.set(true);
    }
  }

  ngOnDestroy(): void {
    this.map?.remove();
    this.map = null;
  }

  /** Current view centre (used to bias search results); null until the map is ready. */
  center(): LatLng | null {
    const c = this.map?.getCenter();
    return c ? { lat: c.lat, lng: wrapLng(c.lng) } : null;
  }

  flyTo(point: LatLng, zoom = 11): void {
    this.fitted = true;
    this.map?.flyTo([point.lat, point.lng], zoom, { duration: 0.6 });
  }

  /** Leaflet needs a nudge when its container becomes visible (e.g. a mobile tab switch). */
  invalidateSize(): void {
    this.map?.invalidateSize();
  }

  private render(markers: readonly MapMarker[], lines: readonly MapLine[]): void {
    const L = this.L;
    if (!L || !this.markerLayer || !this.lineLayer || !this.map) return;
    this.markerLayer.clearLayers();
    this.lineLayer.clearLayers();
    for (const line of lines) {
      if (line.points.length < 2) continue;
      L.polyline(line.points, {
        color: cssColor(line.color),
        weight: 4,
        opacity: 0.85,
        dashArray: line.dashed ? '8 8' : undefined,
      }).addTo(this.lineLayer);
    }
    for (const m of markers) {
      const color = cssColor(m.color);
      L.circleMarker([m.lat, m.lng], {
        radius: m.radius ?? 7,
        color: '#fff',
        weight: 2,
        fillColor: color,
        fillOpacity: 0.95,
      })
        .bindTooltip(escapeHtml(m.label), { direction: 'top', offset: [0, -6] })
        .on('click', (e: Leaflet.LeafletMouseEvent) => {
          L.DomEvent.stopPropagation(e);
          this.markerSelect.emit(m);
        })
        .addTo(this.markerLayer);
    }
    const hasContent = markers.length > 0 || lines.some((l) => l.points.length > 1);
    if (this.autoFit() && hasContent && !this.fitted) {
      this.fitTo(markers, lines, 12);
      this.fitted = true;
    }
  }

  private fitTo(markers: readonly MapMarker[], lines: readonly MapLine[], maxZoom: number): void {
    const L = this.L;
    if (!L || !this.map) return;
    const bounds = L.latLngBounds([
      ...markers.map((m) => [m.lat, m.lng] as [number, number]),
      ...lines.flatMap((l) => l.points),
    ]);
    if (!bounds.isValid()) return;
    this.movingProgrammatically = true;
    this.map.fitBounds(bounds, { padding: [32, 32], maxZoom, animate: false });
    this.movingProgrammatically = false;
  }

  private renderPin(pin: LatLng | null): void {
    const L = this.L;
    if (!L || !this.pinLayer) return;
    this.pinLayer.clearLayers();
    if (!pin) return;
    L.circleMarker([pin.lat, pin.lng], {
      radius: 10,
      color: cssColor('--danger'),
      weight: 3,
      fillColor: '#fff',
      fillOpacity: 1,
    }).addTo(this.pinLayer);
  }
}

function round5(value: number): number {
  return Math.round(value * 1e5) / 1e5;
}

/** Leaflet keeps counting longitude past ±180 after panning around the world. */
function wrapLng(lng: number): number {
  return ((((lng + 180) % 360) + 360) % 360) - 180;
}

function cssColor(value: string): string {
  if (!value.startsWith('--')) return value;
  const resolved = getComputedStyle(document.documentElement).getPropertyValue(value).trim();
  return resolved || '#3366cc';
}

function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
