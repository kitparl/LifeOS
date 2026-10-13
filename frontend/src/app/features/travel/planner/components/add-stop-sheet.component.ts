import { Component, DestroyRef, effect, inject, input, output, signal, untracked } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subject } from 'rxjs';
import { PlanPlace, PlanStop, StopKind } from '../../models/share.models';
import { Suggestion } from '../../models/travel.models';
import { LatLngBias } from '../../utils/place-suggestions';
import { StopFields } from '../plan-ops';
import { COPY, QUICK_CHIPS } from '../planner-copy';
import { PlannerStore } from '../planner-store';
import { looksLikeLink } from '../maps-link';
import { PlannerSheetComponent } from './planner-sheet.component';

/**
 * Adding or changing a stop in a few taps: What, Where, Time, plus quick chips. Where takes a
 * search, or a pasted Google Maps link; everything else waits under "More details".
 */
@Component({
  selector: 'app-planner-add-stop',
  standalone: true,
  imports: [PlannerSheetComponent],
  template: `
    <app-planner-sheet [open]="open()" [heading]="stop() ? copy.sheet.editTitle : copy.sheet.addTitle" (closed)="closed.emit()">
      <form class="form" (submit)="$event.preventDefault(); done()">
        @if (dayLabel()) { <p class="tp-muted">{{ dayLabel() }}</p> }
        <div class="chips" role="group" aria-label="Kind of stop">
          @for (chip of chips; track chip.kind) {
            <button type="button" class="tp-btn chip" [attr.aria-pressed]="kind() === chip.kind" (click)="pickChip(chip.kind, chip.title)">
              <span aria-hidden="true">{{ chip.icon }}</span> {{ chip.label }}
            </button>
          }
        </div>

        <div>
          <label class="tp-label" for="tp-what">{{ copy.sheet.what }}</label>
          <input id="tp-what" class="tp-input" data-testid="stop-what" maxlength="200" autocomplete="off"
            [placeholder]="copy.sheet.whatHint" [value]="title()" (input)="title.set(value($event))" [attr.aria-invalid]="!!error()" [attr.aria-describedby]="error() ? 'tp-what-error' : null" />
          @if (error()) { <p id="tp-what-error" class="error" role="alert">{{ error() }}</p> }
        </div>

        <div class="where">
          <label class="tp-label" for="tp-where">{{ copy.sheet.where }}</label>
          @if (place(); as p) {
            <p class="picked tp-card"><span aria-hidden="true">📍</span><span class="grow">{{ p.name }}</span>
              <button type="button" class="tp-btn tp-btn--quiet" (click)="place.set(null)">{{ copy.sheet.clearPlace }}</button></p>
          } @else {
            <input id="tp-where" class="tp-input" data-testid="stop-where" autocomplete="off" role="combobox"
              aria-autocomplete="list" [attr.aria-expanded]="suggestions().length > 0" aria-controls="tp-where-list"
              [placeholder]="copy.sheet.whereHint" [value]="where()" (input)="onWhere(value($event))" />
            @if (suggestions().length) {
              <ul id="tp-where-list" role="listbox" class="tp-card list">
                @for (s of suggestions(); track s.external_place_id) {
                  <li role="option" aria-selected="false">
                    <button type="button" (click)="pickSuggestion(s)"><strong>{{ s.primary }}</strong> <span class="tp-muted">{{ s.secondary }}</span></button>
                  </li>
                }
              </ul>
            }
          }
          @if (notice()) { <p class="tp-muted" role="status">{{ notice() }}</p> }
        </div>

        <div>
          <label class="tp-label" for="tp-time">{{ copy.sheet.time }}</label>
          <input id="tp-time" class="tp-input time" type="time" [value]="startTime()" (input)="startTime.set(value($event))" />
        </div>

        <details [open]="moreOpen()">
          <summary class="tp-btn tp-btn--quiet">{{ copy.sheet.moreDetails }}</summary>
          <div class="more">
            <label class="tp-label" for="tp-notes">{{ copy.sheet.notes }}</label>
            <textarea id="tp-notes" class="tp-input" rows="3" maxlength="10000" [value]="notes()" (input)="notes.set(value($event))"></textarea>
            <label class="tp-label" for="tp-stay">{{ copy.sheet.stay }}</label>
            <input id="tp-stay" class="tp-input" maxlength="200" [value]="stay()" (input)="stay.set(value($event))" />
            <label class="tp-label" for="tp-transport">{{ copy.sheet.transport }}</label>
            <input id="tp-transport" class="tp-input" maxlength="120" [value]="transport()" (input)="transport.set(value($event))" />
            <label class="tp-label" for="tp-links">{{ copy.sheet.links }}</label>
            <textarea id="tp-links" class="tp-input" rows="2" [value]="links()" (input)="links.set(value($event))"></textarea>
          </div>
        </details>

        <div class="footer">
          @if (stop()) {
            <button type="button" class="tp-btn tp-btn--quiet danger" data-testid="stop-remove" (click)="removed.emit()">{{ copy.remove }}</button>
          }
          <button type="button" class="tp-btn" (click)="closed.emit()">{{ copy.sheet.cancel }}</button>
          <button type="submit" class="tp-btn tp-btn--primary" data-testid="stop-done">{{ copy.sheet.save }}</button>
        </div>
      </form>
    </app-planner-sheet>
  `,
  styles: [
    `
      .form { display: grid; gap: 1rem; }
      .chips { display: flex; flex-wrap: wrap; gap: 0.5rem; }
      .chip[aria-pressed='true'] { background: var(--tp-accent); border-color: var(--tp-accent); color: var(--tp-on-accent); }
      .where { position: relative; }
      .list { list-style: none; margin: 0.25rem 0 0; padding: 0.25rem; max-height: 14rem; overflow-y: auto; }
      .list button { all: unset; display: block; width: 100%; box-sizing: border-box; padding: 0.625rem; border-radius: var(--tp-radius-sm); cursor: pointer; min-height: var(--tp-tap); }
      .list button:hover, .list button:focus-visible { background: var(--tp-surface-2); outline: 3px solid var(--tp-focus); }
      .picked { display: flex; align-items: center; gap: 0.5rem; padding: 0.25rem 0.25rem 0.25rem 0.75rem; margin: 0; }
      .grow { flex: 1; font-weight: 600; }
      .time { max-width: 12rem; }
      .more { display: grid; gap: 0.5rem; padding-top: 0.5rem; }
      summary { list-style: none; padding-left: 0; }
      .footer { display: flex; justify-content: flex-end; flex-wrap: wrap; gap: 0.5rem; position: sticky; bottom: 0; padding-top: 0.5rem; background: var(--tp-surface); }
      .danger { color: var(--tp-danger); margin-right: auto; }
      .error { color: var(--tp-danger); margin-top: 0.25rem; }
    `,
  ],
})
export class PlannerAddStopComponent {
  private readonly store = inject(PlannerStore);
  private readonly query$ = new Subject<string>();

  readonly open = input(false);
  /** The stop being changed, or null to add a new one. */
  readonly stop = input<PlanStop | null>(null);
  readonly dayLabel = input<string | null>(null);
  readonly bias = input<() => LatLngBias>(() => null);
  readonly saved = output<StopFields>();
  readonly removed = output<void>();
  readonly closed = output<void>();

  readonly copy = COPY;
  readonly chips = QUICK_CHIPS;
  readonly title = signal('');
  readonly kind = signal<StopKind>('other');
  readonly where = signal('');
  readonly place = signal<PlanPlace | null>(null);
  readonly startTime = signal('');
  readonly endTime = signal<string | null>(null);
  readonly notes = signal('');
  readonly stay = signal('');
  readonly transport = signal('');
  readonly links = signal('');
  readonly moreOpen = signal(false);
  readonly suggestions = signal<Suggestion[]>([]);
  readonly notice = signal<string | null>(null);
  readonly error = signal<string | null>(null);

  constructor() {
    this.store
      .suggestions(this.query$, () => this.bias()())
      .pipe(takeUntilDestroyed(inject(DestroyRef)))
      .subscribe({
        next: (res) => {
          this.suggestions.set(res.suggestions);
          this.notice.set(res.fallback_reason ? (res.fallback_reason === 'guest_limit' ? COPY.sheet.searchResting : COPY.sheet.searchOff) : null);
        },
        error: () => this.notice.set(COPY.sheet.searchOff),
      });
    // Fill the form each time the sheet opens.
    effect(() => {
      if (!this.open()) return;
      const s = this.stop();
      untracked(() => this.reset(s));
    });
  }

  value(event: Event): string {
    return (event.target as HTMLInputElement).value;
  }

  private reset(s: PlanStop | null): void {
    this.title.set(s?.title ?? '');
    this.kind.set(s?.kind ?? 'other');
    this.place.set(s?.place ?? null);
    this.where.set('');
    this.startTime.set(s?.start_time?.slice(0, 5) ?? '');
    this.endTime.set(s?.end_time ?? null);
    this.notes.set(s?.notes ?? '');
    this.stay.set(s?.stay ?? '');
    this.transport.set(s?.transport ?? '');
    this.links.set((s?.links ?? []).join('\n'));
    this.moreOpen.set(!!(s?.notes || s?.stay || s?.transport || s?.links?.length));
    this.suggestions.set([]);
    this.notice.set(null);
    this.error.set(null);
  }

  pickChip(kind: StopKind, title: string): void {
    this.kind.set(kind);
    if (!this.title().trim()) this.title.set(title);
  }

  async onWhere(text: string): Promise<void> {
    this.where.set(text);
    if (!looksLikeLink(text)) {
      this.query$.next(text);
      return;
    }
    this.suggestions.set([]);
    this.notice.set(COPY.sheet.readingLink);
    const link = await this.store.readLink(text.trim());
    if (link && link.lat !== null && link.lng !== null) {
      this.place.set({ name: link.name || this.title().trim() || 'Pinned place', lat: link.lat, lng: link.lng, google_place_id: link.google_place_id });
      if (!this.title().trim() && link.name) this.title.set(link.name);
      this.notice.set(null);
    } else {
      // Keep the link itself so nothing the friend pasted is lost.
      this.links.set([this.links().trim(), text.trim()].filter(Boolean).join('\n'));
      if (!this.title().trim() && link?.name) this.title.set(link.name);
      this.moreOpen.set(true);
      this.notice.set(COPY.sheet.linkNotRead);
    }
    this.where.set('');
  }

  async pickSuggestion(s: Suggestion): Promise<void> {
    this.suggestions.set([]);
    try {
      const lookup = await this.store.pickSuggestion(s.external_place_id);
      const r = lookup.result;
      if (r) {
        this.place.set({ name: r.name || s.primary, lat: r.lat, lng: r.lng, google_place_id: r.external_place_id ?? s.external_place_id });
        if (!this.title().trim()) this.title.set(s.primary);
        this.notice.set(null);
      } else {
        this.notice.set(lookup.fallback_reason === 'guest_limit' ? COPY.sheet.searchResting : COPY.sheet.searchOff);
      }
    } catch {
      this.notice.set(COPY.sheet.searchOff);
    }
  }

  done(): void {
    const title = this.title().trim() || this.place()?.name || '';
    if (!title) {
      this.error.set(COPY.sheet.needWhat);
      return;
    }
    this.saved.emit({
      title: title.slice(0, 200),
      kind: this.kind(),
      place: this.place(),
      start_time: this.startTime() || null,
      end_time: this.endTime(),
      transport: this.transport().trim() || null,
      stay: this.stay().trim() || null,
      notes: this.notes().trim() || null,
      links: this.links()
        .split(/\s+/)
        .map((l) => l.trim())
        .filter((l) => /^https?:\/\//i.test(l))
        .slice(0, 20),
    });
  }
}
