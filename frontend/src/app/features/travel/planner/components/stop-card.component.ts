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
      <span class="icon" aria-hidden="true">{{ icon() }}</span>
      <div class="body">
        <h4>
          <span class="tp-sr-only">Stop {{ index() + 1 }}:</span>
          <button type="button" class="title" [disabled]="!editable()" (click)="open.emit()">{{ s.title }}</button>
        </h4>
        @if (time()) { <p class="tp-muted">{{ time() }}</p> }
        @if (s.place && s.place.name !== s.title) { <p class="tp-muted">{{ s.place.name }}</p> }
        @if (s.stay) { <p class="tp-muted">🛏️ {{ s.stay }}</p> }
        @if (s.notes) { <p class="notes">{{ s.notes }}</p> }
        @if (mapsUrl()) {
          <a class="maps" [href]="mapsUrl()" target="_blank" rel="noopener noreferrer">{{ copy.openInMaps }}</a>
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
      .card { display: flex; gap: 0.75rem; padding: 0.75rem; border-left: 6px solid var(--day); }
      .icon { font-size: 1.5rem; line-height: 1; padding-top: 0.25rem; }
      .body { flex: 1; min-width: 0; }
      h4 { margin: 0; font-size: var(--tp-text-lg); }
      .title {
        all: unset; cursor: pointer; font-weight: 700; overflow-wrap: anywhere;
        min-height: var(--tp-tap); display: inline-flex; align-items: center;
      }
      .title:disabled { cursor: default; }
      .title:focus-visible { outline: 3px solid var(--tp-focus); border-radius: 6px; }
      .notes { margin-top: 0.25rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; white-space: pre-line; }
      .maps { display: inline-flex; align-items: center; min-height: var(--tp-tap); color: var(--tp-accent); font-weight: 600; }
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
    return start_time ? (end_time ? `${fmt(start_time)} – ${fmt(end_time)}` : fmt(start_time)) : '';
  });
  readonly mapsUrl = computed(() => {
    const place = this.stop().place;
    return place ? openInGoogleMapsUrl({ lat: place.lat, lng: place.lng, external_place_id: place.google_place_id }) : null;
  });
}
