import {
  Component,
  OnDestroy,
  HostListener,
  ViewChild,
  signal,
  inject,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { DatePipe } from '@angular/common';
import { FullCalendarModule, FullCalendarComponent } from '@fullcalendar/angular';
import { CalendarOptions, EventInput, EventApi, DateSelectArg, EventClickArg } from '@fullcalendar/core';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin from '@fullcalendar/interaction';
import { CalendarService } from './services/calendar.service';
import {
  CalendarEvent,
  EventCategory,
  EventCreate,
  EventListItem,
  EVENT_CATEGORIES,
} from './models/calendar.models';

/** Category → display color */
export const CATEGORY_COLORS: Record<EventCategory, string> = {
  personal: '#3b82f6',
  task: '#8b5cf6',
  running: '#22c55e',
  bill: '#ef4444',
  learning: '#f59e0b',
};

interface QuickCreateState {
  startStr: string;   // datetime-local format
  endStr: string;
  allDay: boolean;
}

@Component({
  selector: 'app-calendar-list',
  standalone: true,
  imports: [FullCalendarModule, FormsModule, RouterLink, DatePipe],
  template: `
    <!-- ====== Quick-Create Modal ====== -->
    @if (quickCreate()) {
      <div class="modal-backdrop" (click)="closeQuickCreate()">
        <div class="modal" (click)="$event.stopPropagation()" style="max-width: 440px">
          <div class="modal-header">
            <span>New Event</span>
            <button type="button" class="btn-ghost !px-2 text-xs" (click)="closeQuickCreate()">✕</button>
          </div>
          <form (ngSubmit)="submitQuickCreate()" #qcForm="ngForm">
            <div class="modal-body space-y-3">
              <div>
                <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Title *</label>
                <input
                  type="text"
                  class="input-field w-full"
                  [(ngModel)]="qcTitle"
                  name="title"
                  required
                  placeholder="Event title"
                  autofocus
                />
              </div>

              <div class="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="qcAllDay"
                  [(ngModel)]="qcAllDay"
                  name="allDay"
                  (ngModelChange)="onAllDayChange()"
                />
                <label for="qcAllDay" class="text-sm" style="color: var(--text)">All day</label>
              </div>

              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Start</label>
                  <input
                    [type]="qcAllDay ? 'date' : 'datetime-local'"
                    class="input-field w-full text-sm"
                    [(ngModel)]="qcStart"
                    name="start"
                    required
                  />
                </div>
                <div>
                  <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">End</label>
                  <input
                    [type]="qcAllDay ? 'date' : 'datetime-local'"
                    class="input-field w-full text-sm"
                    [(ngModel)]="qcEnd"
                    name="end"
                  />
                </div>
              </div>

              <div>
                <label class="block text-xs font-medium mb-1" style="color: var(--text-muted)">Category</label>
                <div class="flex flex-wrap gap-1.5">
                  @for (cat of categories; track cat.value) {
                    <button
                      type="button"
                      class="rounded-full px-2.5 py-0.5 text-xs font-medium border transition-all"
                      [style.background]="qcCategory === cat.value ? categoryColor(cat.value) : 'transparent'"
                      [style.color]="qcCategory === cat.value ? '#fff' : 'var(--text-muted)'"
                      [style.border-color]="categoryColor(cat.value)"
                      (click)="qcCategory = cat.value"
                    >
                      {{ cat.label }}
                    </button>
                  }
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn-secondary text-xs" (click)="closeQuickCreate()">Cancel</button>
              <a [routerLink]="['/calendar/new']" class="btn-ghost text-xs no-underline">More options</a>
              <button type="submit" class="btn-primary text-xs" [disabled]="!qcTitle.trim() || saving()">
                {{ saving() ? 'Creating…' : 'Create' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    }

    <!-- ====== Event Detail Modal ====== -->
    @if (detailEvent()) {
      <div class="modal-backdrop" (click)="closeDetail()">
        <div class="modal" (click)="$event.stopPropagation()" style="max-width: 440px">
          <div class="modal-header" style="gap: 0.5rem">
            <span
              class="inline-block w-3 h-3 rounded-full shrink-0"
              [style.background]="categoryColor(detailEvent()!.category)"
            ></span>
            <span class="flex-1 truncate">{{ detailEvent()!.title }}</span>
            <button type="button" class="btn-ghost !px-2 text-xs" (click)="closeDetail()">✕</button>
          </div>
          <div class="modal-body space-y-3 text-sm">
            <!-- Date / time -->
            <div class="flex items-start gap-2" style="color: var(--text-muted)">
              <span>📅</span>
              <span>
                @if (detailEvent()!.all_day) {
                  {{ detailEvent()!.starts_at | date: 'EEEE, MMMM d, y' }}
                  @if (detailEvent()!.ends_at) {
                    &nbsp;– {{ detailEvent()!.ends_at! | date: 'EEEE, MMMM d, y' }}
                  }
                } @else {
                  {{ detailEvent()!.starts_at | date: 'EEE, MMM d · h:mm a' }}
                  @if (detailEvent()!.ends_at) {
                    &nbsp;– {{ detailEvent()!.ends_at! | date: 'h:mm a' }}
                  }
                }
              </span>
            </div>

            <!-- Category -->
            <div class="flex items-center gap-2">
              <span
                class="inline-block px-2 py-0.5 rounded-full text-xs font-medium text-white capitalize"
                [style.background]="categoryColor(detailEvent()!.category)"
              >
                {{ detailEvent()!.category }}
              </span>
              @if (detailEvent()!.recurrence !== 'none') {
                <span class="text-xs" style="color: var(--text-muted)">
                  🔁 {{ detailEvent()!.recurrence }}
                </span>
              }
            </div>

            <!-- Location -->
            @if (detailEvent()!.location) {
              <div class="flex items-start gap-2" style="color: var(--text-muted)">
                <span>📍</span>
                <span>{{ detailEvent()!.location }}</span>
              </div>
            }

            <!-- Description -->
            @if (detailEvent()!.description) {
              <div class="flex items-start gap-2" style="color: var(--text)">
                <span style="color: var(--text-muted)">📝</span>
                <p class="whitespace-pre-wrap">{{ detailEvent()!.description }}</p>
              </div>
            }
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn-ghost text-xs"
              style="color: var(--danger)"
              (click)="deleteEvent(detailEvent()!.id)"
              [disabled]="deleting()"
            >
              {{ deleting() ? 'Deleting…' : 'Delete' }}
            </button>
            <div class="flex-1"></div>
            <a
              [routerLink]="['/calendar', detailEvent()!.id, 'edit']"
              class="btn-secondary text-xs no-underline"
              (click)="closeDetail()"
            >
              Edit
            </a>
            <button type="button" class="btn-primary text-xs" (click)="closeDetail()">Done</button>
          </div>
        </div>
      </div>
    }

    <!-- ====== Calendar ====== -->
    <div class="space-y-0">
      <div class="flex items-center justify-between mb-3">
        <h1 class="text-lg font-semibold">Calendar</h1>
        <div class="flex items-center gap-2">
          @if (keyboardHint()) {
            <span class="hidden sm:inline text-xs" style="color: var(--text-faint)">
              <kbd>n</kbd> new · <kbd>t</kbd> today · <kbd>m/w/d/a</kbd> view
            </span>
          }
          <button
            type="button"
            class="btn-primary text-xs"
            (click)="openNewEventForm()"
          >
            + New event
          </button>
        </div>
      </div>

      <!-- Category legend -->
      <div class="flex flex-wrap gap-1.5 mb-3">
        @for (cat of categories; track cat.value) {
          <span
            class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium text-white"
            [style.background]="categoryColor(cat.value)"
          >
            {{ cat.label }}
          </span>
        }
      </div>

      <div class="calendar-page">
        <full-calendar #calendar [options]="calendarOptions" />
      </div>
    </div>
  `,
})
export class CalendarListComponent implements OnDestroy {
  @ViewChild('calendar') calendarRef!: FullCalendarComponent;

  private readonly calendarService = inject(CalendarService);
  private readonly router = inject(Router);

  readonly categories = EVENT_CATEGORIES;

  // Quick-create modal state
  readonly quickCreate = signal<QuickCreateState | null>(null);
  qcTitle = '';
  qcStart = '';
  qcEnd = '';
  qcAllDay = false;
  qcCategory: EventCategory = 'personal';
  readonly saving = signal(false);

  // Event detail modal state
  readonly detailEvent = signal<CalendarEvent | null>(null);
  readonly deleting = signal(false);

  readonly keyboardHint = signal(true);

  readonly calendarOptions: CalendarOptions = {
    plugins: [dayGridPlugin, timeGridPlugin, listPlugin, interactionPlugin],
    initialView: this.getInitialView(),
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek',
    },
    buttonText: {
      today: 'Today',
      month: 'Month',
      week: 'Week',
      day: 'Day',
      list: 'Agenda',
    },
    selectable: true,
    selectMirror: true,
    editable: true,
    dayMaxEvents: true,
    weekends: true,
    nowIndicator: true,
    scrollTime: '08:00:00',
    events: this.loadEvents.bind(this),
    select: this.handleDateSelect.bind(this),
    eventClick: this.handleEventClick.bind(this),
    eventDrop: this.handleEventDrop.bind(this),
    eventResize: this.handleEventResize.bind(this),
    eventDidMount: this.applyEventColor.bind(this),
  };

  ngOnDestroy(): void { /* cleanup if needed */ }

  categoryColor(cat: EventCategory): string {
    return CATEGORY_COLORS[cat] ?? '#6b7280';
  }

  // ── FullCalendar callbacks ──────────────────────────────────────────────────

  private loadEvents(
    fetchInfo: { startStr: string; endStr: string },
    successCallback: (events: EventInput[]) => void,
    failureCallback: (error: Error) => void,
  ): void {
    this.calendarService.list(fetchInfo.startStr, fetchInfo.endStr).subscribe({
      next: (events) => successCallback(events.map((e) => this.toFCEvent(e))),
      error: (err: Error) => failureCallback(err),
    });
  }

  private toFCEvent(e: EventListItem): EventInput {
    const color = this.categoryColor(e.category);
    const isRoutine = e.source_module === 'routine' || e.id.startsWith('routine:');
    return {
      id: e.id,
      title: e.title,
      start: e.starts_at,
      end: e.ends_at ?? undefined,
      allDay: e.all_day,
      backgroundColor: color,
      borderColor: color,
      editable: !isRoutine,
      startEditable: !isRoutine,
      durationEditable: !isRoutine,
      extendedProps: {
        category: e.category,
        source_module: e.source_module ?? null,
        source_id: e.source_id ?? null,
      },
    };
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private applyEventColor(info: { event: EventApi; el: HTMLElement }): void {
    const cat = info.event.extendedProps['category'] as EventCategory;
    if (cat) {
      const color = this.categoryColor(cat);
      info.el.style.backgroundColor = color;
      info.el.style.borderColor = color;
    }
  }

  handleDateSelect(selectInfo: DateSelectArg): void {
    const start = selectInfo.allDay
      ? selectInfo.startStr
      : this.toLocalDatetimeInput(new Date(selectInfo.start));
    const end = selectInfo.allDay
      ? selectInfo.endStr
      : selectInfo.end
      ? this.toLocalDatetimeInput(new Date(selectInfo.end))
      : '';

    this.qcTitle = '';
    this.qcAllDay = selectInfo.allDay;
    this.qcStart = start;
    this.qcEnd = end;
    this.qcCategory = 'personal';
    this.quickCreate.set({ startStr: start, endStr: end, allDay: selectInfo.allDay });
  }

  handleEventClick(clickInfo: EventClickArg): void {
    clickInfo.jsEvent.preventDefault();
    const id = clickInfo.event.id;
    const sourceModule = clickInfo.event.extendedProps['source_module'] as string | null;

    // Routine expansions: routine:{routineId}:{blockId}:{date}
    if (sourceModule === 'routine' || id.startsWith('routine:')) {
      const parts = id.split(':');
      const routineId = parts.length >= 2 ? parts[1] : null;
      if (routineId) {
        this.router.navigate(['/routines', routineId]);
        return;
      }
    }

    // Recurring calendar expansions use {uuid}:{YYYY-MM-DD}
    const baseId = /^[0-9a-f-]{36}:\d{4}-\d{2}-\d{2}$/i.test(id) ? id.slice(0, 36) : id;

    this.calendarService.get(baseId).subscribe({
      next: (ev) => this.detailEvent.set(ev),
    });
  }

  handleEventDrop(dropInfo: { event: EventApi; revert: () => void }): void {
    const ev = dropInfo.event;
    if (ev.extendedProps['source_module'] === 'routine' || ev.id.startsWith('routine:')) {
      dropInfo.revert();
      return;
    }
    const baseId = /^[0-9a-f-]{36}:\d{4}-\d{2}-\d{2}$/i.test(ev.id) ? ev.id.slice(0, 36) : ev.id;
    this.calendarService
      .update(baseId, {
        starts_at: ev.start!.toISOString(),
        ends_at: ev.end ? ev.end.toISOString() : null,
        all_day: ev.allDay,
      })
      .subscribe({
        error: () => dropInfo.revert(),
      });
  }

  handleEventResize(resizeInfo: { event: EventApi; revert: () => void }): void {
    const ev = resizeInfo.event;
    if (ev.extendedProps['source_module'] === 'routine' || ev.id.startsWith('routine:')) {
      resizeInfo.revert();
      return;
    }
    const baseId = /^[0-9a-f-]{36}:\d{4}-\d{2}-\d{2}$/i.test(ev.id) ? ev.id.slice(0, 36) : ev.id;
    this.calendarService
      .update(baseId, {
        starts_at: ev.start!.toISOString(),
        ends_at: ev.end ? ev.end.toISOString() : null,
      })
      .subscribe({
        error: () => resizeInfo.revert(),
      });
  }

  // ── Quick-create form ───────────────────────────────────────────────────────

  onAllDayChange(): void {
    if (this.qcAllDay) {
      // Strip time component
      this.qcStart = this.qcStart.split('T')[0];
      this.qcEnd = this.qcEnd.split('T')[0];
    } else {
      // Add default time if missing
      if (!this.qcStart.includes('T')) {
        this.qcStart = `${this.qcStart}T09:00`;
      }
      if (!this.qcEnd.includes('T')) {
        this.qcEnd = `${this.qcEnd}T10:00`;
      }
    }
  }

  submitQuickCreate(): void {
    if (!this.qcTitle.trim()) return;
    this.saving.set(true);

    const payload: EventCreate = {
      title: this.qcTitle.trim(),
      starts_at: this.qcAllDay
        ? new Date(this.qcStart + 'T00:00:00').toISOString()
        : new Date(this.qcStart).toISOString(),
      ends_at: this.qcEnd
        ? this.qcAllDay
          ? new Date(this.qcEnd + 'T23:59:59').toISOString()
          : new Date(this.qcEnd).toISOString()
        : null,
      all_day: this.qcAllDay,
      category: this.qcCategory,
    };

    this.calendarService.create(payload).subscribe({
      next: () => {
        this.saving.set(false);
        this.closeQuickCreate();
        this.calendarRef.getApi().refetchEvents();
      },
      error: () => this.saving.set(false),
    });
  }

  closeQuickCreate(): void {
    this.quickCreate.set(null);
    this.calendarRef?.getApi().unselect();
  }

  // ── Event detail modal ──────────────────────────────────────────────────────

  closeDetail(): void {
    this.detailEvent.set(null);
  }

  deleteEvent(id: string): void {
    this.deleting.set(true);
    this.calendarService.delete(id).subscribe({
      next: () => {
        this.deleting.set(false);
        this.closeDetail();
        this.calendarRef.getApi().refetchEvents();
      },
      error: () => this.deleting.set(false),
    });
  }

  openNewEventForm(): void {
    // Navigate to full form — handled by routerLink, but we can also open quick-create
    const now = new Date();
    const start = this.toLocalDatetimeInput(now);
    const end = this.toLocalDatetimeInput(new Date(now.getTime() + 60 * 60 * 1000));
    this.qcTitle = '';
    this.qcAllDay = false;
    this.qcStart = start;
    this.qcEnd = end;
    this.qcCategory = 'personal';
    this.quickCreate.set({ startStr: start, endStr: end, allDay: false });
  }

  // ── Keyboard shortcuts ──────────────────────────────────────────────────────

  @HostListener('window:keydown', ['$event'])
  onKeydown(e: KeyboardEvent): void {
    // Ignore when typing in an input/modal
    const target = e.target as HTMLElement;
    const inInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName);
    if (inInput || this.quickCreate() || this.detailEvent()) return;

    const api = this.calendarRef?.getApi();
    if (!api) return;

    switch (e.key) {
      case 't':
        api.today();
        break;
      case 'm':
        api.changeView('dayGridMonth');
        break;
      case 'w':
        api.changeView('timeGridWeek');
        break;
      case 'd':
        api.changeView('timeGridDay');
        break;
      case 'a':
        api.changeView('listWeek');
        break;
      case 'ArrowLeft':
        api.prev();
        break;
      case 'ArrowRight':
        api.next();
        break;
      case 'n':
      case 'c':
        this.openNewEventForm();
        break;
    }
  }

  // ── Helpers ─────────────────────────────────────────────────────────────────

  private getInitialView(): string {
    if (typeof window === 'undefined') return 'dayGridMonth';
    return window.innerWidth < 768 ? 'listWeek' : 'dayGridMonth';
  }

  private toLocalDatetimeInput(date: Date): string {
    const pad = (n: number) => String(n).padStart(2, '0');
    return (
      `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
      `T${pad(date.getHours())}:${pad(date.getMinutes())}`
    );
  }
}
