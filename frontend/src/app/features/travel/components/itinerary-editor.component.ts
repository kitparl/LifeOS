import { CdkDrag, CdkDragDrop, CdkDragHandle, CdkDropList, CdkDropListGroup } from '@angular/cdk/drag-drop';
import { DatePipe } from '@angular/common';
import { Component, computed, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ItemUpdate, ItineraryDay, ItineraryItem, TripPlace } from '../models/travel.models';
import { dayEndpoints, moveItem } from '../utils/itinerary';

export interface ItemPatch {
  id: string;
  patch: ItemUpdate;
}

export interface NewItem {
  day_id: string;
  title: string;
  place_id: string | null;
}

/**
 * Day-by-day itinerary (spec §11). Presentational: every change is emitted and the page saves it.
 * Dragging within or across days emits the whole layout once (one request per drag); field edits
 * save on change, so there is no Save button (drafts autosave, requirements D-12).
 */
@Component({
  selector: 'app-itinerary-editor',
  standalone: true,
  imports: [FormsModule, DatePipe, CdkDropListGroup, CdkDropList, CdkDrag, CdkDragHandle],
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
              <li class="rounded p-2" style="background: var(--surface)" cdkDrag [cdkDragData]="item">
                <div class="flex items-start gap-2">
                  <span cdkDragHandle class="cursor-grab select-none" aria-label="Drag to reorder" title="Drag to reorder">⠿</span>
                  <div class="min-w-0 flex-1">
                    <button type="button" class="text-left" (click)="toggle(item.id)">
                      @if (item.start_time) {
                        <span class="text-xs" style="color: var(--text-muted)">{{ item.start_time.slice(0, 5) }}</span>
                      }
                      <span class="font-medium">{{ item.title }}</span>
                      @if (placeName(item); as p) {
                        <span class="text-xs" style="color: var(--text-muted)"> · 📍 {{ p }}</span>
                      }
                      @if (endpoints().get(item.id); as label) {
                        <span class="chip ml-1 text-xs">{{ label }}</span>
                      }
                    </button>
                    @if (open() === item.id) {
                      <div class="mt-2 grid gap-2 sm:grid-cols-2">
                        <input class="input-field text-xs sm:col-span-2" maxlength="200" aria-label="Activity" [ngModel]="item.title" (change)="patch(item, { title: val($event) })" />
                        <label class="text-xs">Start
                          <input class="input-field text-xs" type="time" [ngModel]="item.start_time?.slice(0, 5)" (change)="patch(item, { start_time: val($event) || null })" />
                        </label>
                        <label class="text-xs">End
                          <input class="input-field text-xs" type="time" [ngModel]="item.end_time?.slice(0, 5)" (change)="patch(item, { end_time: val($event) || null })" />
                        </label>
                        <label class="text-xs sm:col-span-2">Place
                          <select class="input-field text-xs" [ngModel]="item.place_id ?? ''" (change)="patch(item, { place_id: val($event) || null })">
                            <option value="">No place</option>
                            @for (p of places(); track p.id) {
                              <option [value]="p.id">{{ p.name }}</option>
                            }
                          </select>
                        </label>
                        <input class="input-field text-xs" maxlength="120" placeholder="Transport" aria-label="Transport" [ngModel]="item.transport ?? ''" (change)="patch(item, { transport: val($event) || null })" />
                        <input class="input-field text-xs" maxlength="200" placeholder="Accommodation" aria-label="Accommodation" [ngModel]="item.accommodation ?? ''" (change)="patch(item, { accommodation: val($event) || null })" />
                        <textarea class="input-field text-xs sm:col-span-2" rows="2" placeholder="Notes" aria-label="Notes" [ngModel]="item.notes ?? ''" (change)="patch(item, { notes: val($event) || null })"></textarea>
                        <div class="flex flex-wrap gap-2 sm:col-span-2">
                          <label class="text-xs">Move to
                            <select class="input-field !w-auto text-xs" [ngModel]="day.id" (change)="moveTo(item, day.id, val($event))">
                              @for (d of days(); track d.id) {
                                <option [value]="d.id">Day {{ d.day_index + 1 }}</option>
                              }
                            </select>
                          </label>
                          <button type="button" class="text-xs" style="color: var(--danger)" (click)="deleteItem.emit(item.id)">Delete stop</button>
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

  readonly reorder = output<Record<string, string[]>>();
  readonly itemPatch = output<ItemPatch>();
  readonly deleteItem = output<string>();
  readonly addItem = output<NewItem>();
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

  toggle(id: string): void {
    this.open.set(this.open() === id ? null : id);
  }

  placeName(item: ItineraryItem): string | null {
    return this.places().find((p) => p.id === item.place_id)?.name ?? null;
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

  add(dayId: string): void {
    const placeId = this.draftPlaces[dayId] || null;
    const title = (this.drafts[dayId] ?? '').trim() || this.places().find((p) => p.id === placeId)?.name || '';
    if (!title) return;
    this.addItem.emit({ day_id: dayId, title, place_id: placeId });
    this.drafts[dayId] = '';
    this.draftPlaces[dayId] = '';
  }
}
