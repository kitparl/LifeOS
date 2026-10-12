import { CdkDrag, CdkDragDrop, CdkDragHandle, CdkDropList, CdkDropListGroup } from '@angular/cdk/drag-drop';
import { DatePipe } from '@angular/common';
import { Component, ElementRef, computed, effect, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LatLng } from '../map/travel-map.component';
import { GeoLookup, ItemUpdate, ItineraryDay, ItineraryItem, PlaceChoice, TripPlace } from '../models/travel.models';
import { dayEndpoints, moveItem, searchBias } from '../utils/itinerary';
import { PickedPlace, PlaceSearchComponent } from './place-search.component';

export interface ItemPatch {
  id: string;
  patch: ItemUpdate;
}

export interface NewItem {
  day_id: string;
  title: string;
  place_id: string | null;
}

export interface PlaceChange {
  id: string;
  pick: PlaceChoice;
  /** New title when it still mirrors the old place name; otherwise the user's own title is kept. */
  title?: string;
}

export interface NewCheckpoints {
  day_id: string;
  /** In the order they were picked: start, vias, end. */
  picks: PlaceChoice[];
}

/**
 * Day-by-day itinerary (spec §11). Presentational: every change is emitted and the page saves it.
 * Dragging within or across days emits the whole layout once (one request per drag); field edits
 * save on change, so there is no Save button (drafts autosave, requirements D-12).
 */
@Component({
  selector: 'app-itinerary-editor',
  standalone: true,
  imports: [FormsModule, DatePipe, CdkDropListGroup, CdkDropList, CdkDrag, CdkDragHandle, PlaceSearchComponent],
  template: `
    <div class="space-y-3" cdkDropListGroup>
      @for (day of days(); track day.id) {
        <section class="panel space-y-2 text-sm">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <p class="font-medium">
              Day {{ day.day_index + 1 }}
              @if (day.day_date) {
                <span style="color: var(--text-muted)">· {{ day.day_date | date: 'EEE, MMM d' }}</span>
              }
            </p>
            <div class="flex items-center gap-2">
              <input
                class="input-field !w-40 text-xs"
                maxlength="200"
                placeholder="Day title"
                [ngModel]="day.title ?? ''"
                (change)="dayTitle.emit({ id: day.id, title: $any($event.target).value })"
                [attr.aria-label]="'Title for day ' + (day.day_index + 1)"
              />
              <button type="button" class="text-xs" style="color: var(--danger)" [disabled]="disabled()" (click)="deleteDay.emit(day.id)">Remove day</button>
            </div>
          </div>

          <ol
            class="min-h-[2.5rem] space-y-1 rounded border border-dashed p-1"
            style="border-color: var(--border)"
            cdkDropList
            [cdkDropListData]="day.id"
            [cdkDropListDisabled]="disabled()"
            (cdkDropListDropped)="drop($event)"
          >
            @for (item of day.items; track item.id) {
              <li
                class="rounded p-2"
                style="background: var(--surface)"
                cdkDrag
                (keydown.escape)="open() === item.id && open.set(null)"
                [cdkDragData]="item"
                [attr.data-place-id]="item.place_id"
                [style.outline]="item.place_id && item.place_id === highlightPlaceId() ? '2px solid var(--primary)' : null"
              >
                <div class="flex items-start gap-2">
                  <span cdkDragHandle class="cursor-grab select-none pt-0.5" style="color: var(--text-muted)" aria-label="Drag to reorder" title="Drag to reorder">⠿</span>
                  <div class="min-w-0 flex-1">
                    <button
                      type="button"
                      class="flex w-full items-start justify-between gap-2 text-left"
                      [attr.aria-expanded]="open() === item.id"
                      [title]="open() === item.id ? 'Collapse' : 'Edit stop'"
                      (click)="toggle(item.id)"
                    >
                      <span class="min-w-0">
                        <span class="font-medium">{{ item.title }}</span>
                        @if (endpoints().get(item.id); as label) {
                          <span class="chip ml-1 text-xs">{{ label }}</span>
                        }
                        @if (summary(item); as line) {
                          <span class="block truncate text-xs" style="color: var(--text-muted)">{{ line }}</span>
                        }
                      </span>
                      <span class="shrink-0 text-xs transition-transform" style="color: var(--text-muted)" [style.transform]="open() === item.id ? 'rotate(180deg)' : null" aria-hidden="true">▾</span>
                    </button>
                    @if (open() === item.id) {
                      <div class="mt-3 space-y-3 border-t pt-3" style="border-color: var(--border)">
                        <label class="block text-xs font-medium" style="color: var(--text-muted)">Activity
                          <input class="input-field mt-1 text-sm" maxlength="200" [ngModel]="item.title" (change)="patch(item, { title: val($event) })" />
                        </label>

                        <div class="space-y-1">
                          <p class="text-xs font-medium" style="color: var(--text-muted)">Location</p>
                          <select class="input-field text-sm" aria-label="Place" [ngModel]="item.place_id ?? ''" (change)="patch(item, { place_id: val($event) || null })">
                            <option value="">No place</option>
                            @for (p of places(); track p.id) {
                              <option [value]="p.id">{{ p.name }}</option>
                            }
                          </select>
                          <app-place-search
                            placeholder="Or search to change the location"
                            [tripPlaces]="places()"
                            [includeSaved]="true"
                            [clearOnPick]="true"
                            [bias]="biasFor(day)"
                            (pickedPlace)="changePlace(item, { placeId: $event.id, name: $event.name })"
                            (picked)="changeLookup(item, $event)"
                          />
                        </div>

                        <div class="grid grid-cols-2 gap-2">
                          <label class="text-xs font-medium" style="color: var(--text-muted)">Start
                            <input class="input-field mt-1 text-sm" type="time" [ngModel]="item.start_time?.slice(0, 5)" (change)="patch(item, { start_time: val($event) || null })" />
                          </label>
                          <label class="text-xs font-medium" style="color: var(--text-muted)">End
                            <input class="input-field mt-1 text-sm" type="time" [ngModel]="item.end_time?.slice(0, 5)" (change)="patch(item, { end_time: val($event) || null })" />
                          </label>
                          <label class="text-xs font-medium" style="color: var(--text-muted)">Transport
                            <input class="input-field mt-1 text-sm" maxlength="120" placeholder="e.g. Taxi" [ngModel]="item.transport ?? ''" (change)="patch(item, { transport: val($event) || null })" />
                          </label>
                          <label class="text-xs font-medium" style="color: var(--text-muted)">Stay
                            <input class="input-field mt-1 text-sm" maxlength="200" placeholder="e.g. Hotel name" [ngModel]="item.accommodation ?? ''" (change)="patch(item, { accommodation: val($event) || null })" />
                          </label>
                        </div>

                        <label class="block text-xs font-medium" style="color: var(--text-muted)">Notes
                          <textarea class="input-field mt-1 text-sm" rows="2" [ngModel]="item.notes ?? ''" (change)="patch(item, { notes: val($event) || null })"></textarea>
                        </label>

                        <div class="flex flex-wrap items-center justify-between gap-2 border-t pt-3" style="border-color: var(--border)">
                          <div class="flex items-center gap-3">
                            <label class="flex items-center gap-1.5 text-xs" style="color: var(--text-muted)">Move to
                              <select class="input-field !w-auto text-xs" [ngModel]="day.id" (change)="moveTo(item, day.id, val($event))">
                                @for (d of days(); track d.id) {
                                  <option [value]="d.id">Day {{ d.day_index + 1 }}</option>
                                }
                              </select>
                            </label>
                            <button type="button" class="text-xs" style="color: var(--danger)" (click)="deleteItem.emit(item.id)">Delete stop</button>
                          </div>
                          <button type="button" class="btn-secondary text-xs" (click)="open.set(null)">Done</button>
                        </div>
                      </div>
                    }
                  </div>
                </div>
              </li>
            } @empty {
              <li class="p-1 text-xs" style="color: var(--text-muted)">Nothing planned yet — drop a stop here or add one.</li>
            }
          </ol>

          <div class="space-y-1">
            <app-place-search
              placeholder="Search to add checkpoints (start, stops, end)"
              [tripPlaces]="places()"
              [includeSaved]="true"
              [clearOnPick]="true"
              [bias]="biasFor(day)"
              (pickedPlace)="queuePlace(day.id, $event)"
              (picked)="queueLookup(day.id, $event)"
            />
            @let picks = queued(day.id);
            @if (picks.length) {
              <div class="flex flex-wrap items-center gap-1.5">
                @for (pick of picks; track $index) {
                  <span class="chip text-xs">
                    {{ $index + 1 }}. {{ pick.name }}
                    <button type="button" class="ml-1" [attr.aria-label]="'Remove ' + pick.name + ' from the checkpoints'" (click)="unqueue(day.id, $index)">×</button>
                  </span>
                }
                <button type="button" class="btn-primary text-xs" [disabled]="disabled()" (click)="submitQueue(day.id)">
                  Add {{ picks.length }} {{ picks.length === 1 ? 'checkpoint' : 'checkpoints' }}
                </button>
              </div>
            }
          </div>

          <form class="flex flex-wrap gap-2" (submit)="$event.preventDefault(); add(day.id)">
            <input class="input-field min-w-[8rem] flex-1 text-xs" maxlength="200" placeholder="Add activity (e.g. Start trek)" [(ngModel)]="drafts[day.id]" [name]="'new-' + day.id" />
            <select class="input-field !w-auto text-xs" [(ngModel)]="draftPlaces[day.id]" [name]="'place-' + day.id" aria-label="Place for new stop">
              <option value="">No place</option>
              @for (p of places(); track p.id) {
                <option [value]="p.id">{{ p.name }}</option>
              }
            </select>
            <button type="submit" class="btn-secondary text-xs" [disabled]="disabled()">Add</button>
          </form>
        </section>
      } @empty {
        <p class="text-xs" style="color: var(--text-muted)">No days yet.</p>
      }
      <div class="flex flex-wrap gap-2">
        <button type="button" class="btn-secondary text-xs" [disabled]="disabled()" (click)="addDay.emit()">+ Add day</button>
        @if (canFill()) {
          <button type="button" class="btn-secondary text-xs" [disabled]="disabled()" (click)="fillDays.emit()">Create a day for every date</button>
        }
      </div>
    </div>
  `,
})
export class ItineraryEditorComponent {
  readonly days = input.required<readonly ItineraryDay[]>();
  readonly places = input.required<readonly TripPlace[]>();
  readonly canFill = input(false);
  readonly disabled = input(false);
  /** Where the trip map is looking; the fallback when a day has no pins to bias place search. */
  readonly mapCenter = input<() => LatLng | null>(() => null);
  /** Items at this place get an outline (a marker was clicked on the map). */
  readonly highlightPlaceId = input<string | null>(null);

  readonly reorder = output<Record<string, string[]>>();
  readonly itemPatch = output<ItemPatch>();
  readonly deleteItem = output<string>();
  readonly addItem = output<NewItem>();
  readonly addCheckpoints = output<NewCheckpoints>();
  readonly itemPlace = output<PlaceChange>();
  readonly addDay = output<void>();
  readonly fillDays = output<void>();
  readonly deleteDay = output<string>();
  readonly dayTitle = output<{ id: string; title: string }>();

  readonly open = signal<string | null>(null);

  /** "Day start" / "Day end" tags on each day's first and last stop with a place. */
  readonly endpoints = computed(() => {
    const labels = new Map<string, string>();
    for (const day of this.days()) {
      const ends = dayEndpoints(day);
      if (!ends) continue;
      labels.set(ends.start.id, 'Day start');
      labels.set(ends.end.id, 'Day end');
    }
    return labels;
  });
  drafts: Record<string, string> = {};
  draftPlaces: Record<string, string> = {};
  /** Checkpoints picked per day but not added yet. */
  readonly queue = signal<Record<string, PlaceChoice[]>>({});
  private readonly biasFns = new Map<string, () => LatLng | null>();
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);

  constructor() {
    effect(() => {
      const id = this.highlightPlaceId();
      if (id) setTimeout(() => this.host.nativeElement.querySelector(`[data-place-id="${id}"]`)?.scrollIntoView?.({ block: 'nearest' }));
    });
  }

  toggle(id: string): void {
    this.open.set(this.open() === id ? null : id);
  }

  /** One muted line under the title: time range, place and transport, so a collapsed stop still says a lot. */
  summary(item: ItineraryItem): string {
    const start = item.start_time?.slice(0, 5);
    const end = item.end_time?.slice(0, 5);
    const time = start && end ? `${start}–${end}` : start ?? (end ? `until ${end}` : null);
    const place = this.placeName(item);
    return [time, place && `📍 ${place}`, item.transport].filter(Boolean).join(' · ');
  }

  placeName(item: ItineraryItem): string | null {
    return this.places().find((p) => p.id === item.place_id)?.name ?? null;
  }

  changePlace(item: ItineraryItem, pick: PlaceChoice): void {
    const oldName = this.placeName(item);
    this.itemPlace.emit({ id: item.id, pick, title: oldName && item.title === oldName ? pick.name : undefined });
  }

  changeLookup(item: ItineraryItem, lookup: GeoLookup): void {
    if (lookup.result) this.changePlace(item, { lookup, name: lookup.result.name });
  }

  val(event: Event): string {
    return (event.target as HTMLInputElement).value.trim();
  }

  patch(item: ItineraryItem, patch: ItemUpdate): void {
    if (patch.title === '') return; // a stop always needs a name
    this.itemPatch.emit({ id: item.id, patch });
  }

  drop(event: CdkDragDrop<string, string, ItineraryItem>): void {
    const from = { dayId: event.previousContainer.data, index: event.previousIndex };
    const to = { dayId: event.container.data, index: event.currentIndex };
    if (from.dayId === to.dayId && from.index === to.index) return;
    this.reorder.emit(moveItem(this.days(), from, to));
  }

  moveTo(item: ItineraryItem, fromDay: string, toDay: string): void {
    if (fromDay === toDay) return;
    const day = this.days().find((d) => d.id === fromDay);
    const index = day?.items.findIndex((i) => i.id === item.id) ?? -1;
    const target = this.days().find((d) => d.id === toDay);
    this.reorder.emit(moveItem(this.days(), { dayId: fromDay, index }, { dayId: toDay, index: target?.items.length ?? 0 }));
  }

  /** One stable function per day (a new one on every change detection would re-trigger the input). */
  biasFor(day: ItineraryDay): () => LatLng | null {
    let fn = this.biasFns.get(day.id);
    if (!fn) {
      fn = () => {
        const current = this.days().find((d) => d.id === day.id) ?? day;
        return searchBias(current, this.places()) ?? this.mapCenter()();
      };
      this.biasFns.set(day.id, fn);
    }
    return fn;
  }

  queuePlace(dayId: string, place: PickedPlace): void {
    this.enqueue(dayId, { placeId: place.id, name: place.name });
  }

  queueLookup(dayId: string, lookup: GeoLookup): void {
    if (lookup.result) this.enqueue(dayId, { lookup, name: lookup.result.name });
  }

  queued(dayId: string): PlaceChoice[] {
    return this.queue()[dayId] ?? [];
  }

  unqueue(dayId: string, index: number): void {
    this.queue.update((q) => ({ ...q, [dayId]: (q[dayId] ?? []).filter((_, i) => i !== index) }));
  }

  submitQueue(dayId: string): void {
    const picks = this.queued(dayId);
    if (!picks.length) return;
    this.addCheckpoints.emit({ day_id: dayId, picks });
    this.queue.update((q) => ({ ...q, [dayId]: [] }));
  }

  private enqueue(dayId: string, pick: PlaceChoice): void {
    this.queue.update((q) => ({ ...q, [dayId]: [...(q[dayId] ?? []), pick] }));
  }

  add(dayId: string): void {
    const placeId = this.draftPlaces[dayId] || null;
    const title = (this.drafts[dayId] ?? '').trim() || this.places().find((p) => p.id === placeId)?.name || '';
    if (!title) return;
    this.addItem.emit({ day_id: dayId, title, place_id: placeId });
    this.drafts[dayId] = '';
    this.draftPlaces[dayId] = '';
  }
}
