import { CdkDragHandle } from '@angular/cdk/drag-drop';
import { Component, computed, input, output } from '@angular/core';
import { PlanStop } from '../../models/share.models';
import { openInGoogleMapsUrl } from '../../utils/google-links';
import { COPY, KIND_ICONS } from '../planner-copy';

/** One stop. Moving works three ways: drag handle, up / down buttons, arrow keys on the handle. */
@Component({
  selector: 'app-planner-stop-card',
  standalone: true,
  imports: [CdkDragHandle],
  template: `
    @let s = stop();
    <article class="tp-card card" [style.--day]="color()">
      <div class="body">
        <h4>
          <span class="icon" aria-hidden="true">{{ icon() }}</span>
          <span class="tp-sr-only">Stop {{ index() + 1 }}:</span>
          <button type="button" class="title" [disabled]="!editable()" (click)="open.emit()">{{ s.title }}</button>
        </h4>
        @if (hasFacts()) {
          <ul class="facts">
            @if (time()) { <li data-testid="stop-time"><span aria-hidden="true">🕘</span> {{ time() }}</li> }
            @if (s.place && s.place.name !== s.title) { <li><span aria-hidden="true">📍</span> {{ s.place.name }}</li> }
            @if (s.transport) { <li><span aria-hidden="true">🚗</span> <span class="label">{{ copy.gettingThere }}:</span> {{ s.transport }}</li> }
            @if (s.stay) { <li><span aria-hidden="true">🛏️</span> <span class="label">{{ copy.stayLabel }}:</span> {{ s.stay }}</li> }
          </ul>
        }
        @if (s.notes) { <p class="notes">{{ s.notes }}</p> }
        @if (mapsUrl() || s.links.length) {
          <p class="links">
            @if (mapsUrl()) {
              <a class="maps" [href]="mapsUrl()" target="_blank" rel="noopener noreferrer">{{ copy.openInMaps }}</a>
            }
            @for (link of s.links; track $index) {
              <a [href]="link" target="_blank" rel="noopener noreferrer" data-testid="stop-link">🔗 {{ site(link) }}</a>
            }
          </p>
        }
      </div>
      @if (editable()) {
        <div class="moves">
          <button type="button" class="tp-btn tp-btn--quiet" data-testid="stop-up" [disabled]="first()" [attr.aria-label]="copy.moveUp(s.title)" (click)="nudge.emit(-1)">↑</button>
          <button
            type="button"
            class="tp-btn tp-btn--quiet handle"
            cdkDragHandle
            [attr.aria-label]="copy.dragHandle(s.title)"
            (keydown.arrowup)="$event.preventDefault(); nudge.emit(-1)"
            (keydown.arrowdown)="$event.preventDefault(); nudge.emit(1)"
          >⠿</button>
          <button type="button" class="tp-btn tp-btn--quiet" data-testid="stop-down" [disabled]="last()" [attr.aria-label]="copy.moveDown(s.title)" (click)="nudge.emit(1)">↓</button>
        </div>
      }
    </article>
  `,
  styles: [
    `
      .card { display: flex; gap: 0.5rem; padding: 0.75rem 0.5rem 0.75rem 1rem; border-left: 4px solid var(--day); }
      .body { flex: 1; min-width: 0; display: grid; gap: 0.375rem; align-content: start; }
      h4 { margin: 0; display: flex; align-items: center; gap: 0.5rem; font-size: var(--tp-text-lg); }
      .icon { font-size: 1.25rem; line-height: 1; }
      .title {
        all: unset; cursor: pointer; font-weight: 700; overflow-wrap: anywhere;
        min-height: var(--tp-tap); display: inline-flex; align-items: center;
      }
      .title:disabled { cursor: default; }
      .title:focus-visible { outline: 3px solid var(--tp-focus); border-radius: 6px; }
      .facts { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.25rem; color: var(--tp-muted); font-size: 0.9375rem; }
      .facts li { overflow-wrap: anywhere; }
      .label { font-weight: 600; }
      .notes {
        padding: 0.5rem 0.75rem; border-radius: var(--tp-radius-sm); background: var(--tp-surface-2);
        display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; white-space: pre-line;
      }
      .links { display: flex; flex-wrap: wrap; gap: 0 1rem; }
      .links a { display: inline-flex; align-items: center; min-height: 2.25rem; color: var(--tp-accent); font-weight: 600; overflow-wrap: anywhere; }
      .moves { display: flex; flex-direction: column; align-items: center; }
      .moves .tp-btn { min-width: var(--tp-tap); padding: 0; font-size: 1.25rem; }
      .handle { cursor: grab; touch-action: none; }
    `,
  ],
})
export class PlannerStopCardComponent {
  readonly stop = input.required<PlanStop>();
  readonly index = input.required<number>();
  readonly first = input(false);
  readonly last = input(false);
  readonly color = input.required<string>();
  readonly editable = input(false);
  readonly open = output<void>();
  readonly nudge = output<-1 | 1>();
  readonly copy = COPY;

  readonly icon = computed(() => KIND_ICONS[this.stop().kind] ?? KIND_ICONS.other);
  readonly time = computed(() => {
    const { start_time, end_time } = this.stop();
    const fmt = (t: string | null) => (t ? t.slice(0, 5) : '');
    if (start_time) return end_time ? `${fmt(start_time)} – ${fmt(end_time)}` : fmt(start_time);
    return end_time ? `until ${fmt(end_time)}` : '';
  });
  readonly hasFacts = computed(() => {
    const s = this.stop();
    return !!(this.time() || (s.place && s.place.name !== s.title) || s.transport || s.stay);
  });
  readonly mapsUrl = computed(() => {
    const place = this.stop().place;
    return place ? openInGoogleMapsUrl({ lat: place.lat, lng: place.lng, external_place_id: place.google_place_id }) : null;
  });

  /** A link's site name, like the PDF guide prints it. */
  site(url: string): string {
    try {
      return new URL(url).hostname.replace(/^www\./, '') || url;
    } catch {
      return url;
    }
  }
}
