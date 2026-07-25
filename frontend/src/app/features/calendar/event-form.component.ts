import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import {
  EVENT_CATEGORIES,
  EVENT_KINDS,
  EVENT_RECURRENCE,
  EventCategory,
  EventKind,
  EventRecurrence,
} from './models/calendar.models';
import { CalendarService } from './services/calendar.service';

@Component({
  selector: 'app-event-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="max-w-lg">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">{{ isEdit ? 'Edit Event' : 'New Event' }}</div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div>
            <label class="mb-1 block">Title</label>
            <input class="input-field" formControlName="title" />
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="mb-1 block">Category</label>
              <select class="input-field" formControlName="category">
                @for (c of categories; track c.value) {
                  <option [value]="c.value">{{ c.label }}</option>
                }
              </select>
            </div>
            <div>
              <label class="mb-1 block">Recurrence</label>
              <select class="input-field" formControlName="recurrence">
                @for (r of recurrences; track r.value) {
                  <option [value]="r.value">{{ r.label }}</option>
                }
              </select>
            </div>
          </div>
          <div>
            <label class="mb-1 block">Event kind</label>
            <select class="input-field" formControlName="event_kind" (change)="onKindChange()">
              @for (k of kinds; track k.value) {
                <option [value]="k.value">{{ k.label }}</option>
              }
            </select>
            <p class="text-xs mt-1" style="color: var(--text-muted)">
              @if (isBirthday) {
                Use the birthday date (month/day). Year is only an anchor. All-day is recommended.
              } @else {
                Birthday forces yearly recurrence and the birthday reminder ladder.
              }
            </p>
          </div>
          <div>
            <label class="mb-1 block">Starts</label>
            <input
              class="input-field"
              [type]="useDateInputs ? 'date' : 'datetime-local'"
              formControlName="starts_at"
            />
          </div>
          <div>
            <label class="mb-1 block">Ends</label>
            <input
              class="input-field"
              [type]="useDateInputs ? 'date' : 'datetime-local'"
              formControlName="ends_at"
            />
          </div>
          <label class="flex items-center gap-2">
            <input type="checkbox" formControlName="all_day" (change)="onAllDayChange()" />
            All day
          </label>
          <div>
            <label class="mb-1 block">Location</label>
            <input class="input-field" formControlName="location" />
          </div>
          <div>
            <label class="mb-1 block">Description</label>
            <textarea class="input-field min-h-[80px]" formControlName="description"></textarea>
          </div>
          @if (error) {
            <p class="text-xs" style="color: var(--danger)">{{ error }}</p>
          }
          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">
              {{ saving ? 'Saving…' : 'Save' }}
            </button>
            <a routerLink="/calendar" class="btn-secondary no-underline">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  `,
})
export class EventFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly calendarService = inject(CalendarService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  categories = EVENT_CATEGORIES;
  recurrences = EVENT_RECURRENCE;
  kinds = EVENT_KINDS;
  isEdit = false;
  eventId: string | null = null;
  saving = false;
  error = '';

  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    category: ['personal' as EventCategory, Validators.required],
    recurrence: ['none' as EventRecurrence, Validators.required],
    event_kind: ['normal' as EventKind, Validators.required],
    starts_at: ['', Validators.required],
    ends_at: [''],
    all_day: [false],
    location: [''],
    description: [''],
  });

  get isBirthday(): boolean {
    return this.form.controls.event_kind.value === 'birthday';
  }

  get useDateInputs(): boolean {
    return this.isBirthday || this.form.controls.all_day.value;
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.eventId = id;
      this.calendarService.get(id).subscribe({
        next: (event) => {
          const useDate = event.all_day || event.event_kind === 'birthday';
          this.form.patchValue({
            title: event.title,
            category: event.category,
            recurrence: event.recurrence,
            event_kind: event.event_kind ?? 'normal',
            starts_at: useDate ? event.starts_at.slice(0, 10) : event.starts_at.slice(0, 16),
            ends_at: event.ends_at
              ? useDate
                ? event.ends_at.slice(0, 10)
                : event.ends_at.slice(0, 16)
              : '',
            all_day: event.all_day || event.event_kind === 'birthday',
            location: event.location ?? '',
            description: event.description ?? '',
          });
        },
      });
    } else if (!this.isEdit) {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(9, 0, 0, 0);
      this.form.patchValue({ starts_at: tomorrow.toISOString().slice(0, 16) });
    }
  }

  onKindChange(): void {
    if (this.form.controls.event_kind.value === 'birthday') {
      const starts = this.form.controls.starts_at.value;
      this.form.patchValue({
        recurrence: 'yearly',
        all_day: true,
        starts_at: starts ? starts.slice(0, 10) : starts,
        ends_at: this.form.controls.ends_at.value
          ? this.form.controls.ends_at.value.slice(0, 10)
          : '',
      });
    }
  }

  onAllDayChange(): void {
    const starts = this.form.controls.starts_at.value;
    const ends = this.form.controls.ends_at.value;
    if (this.form.controls.all_day.value) {
      this.form.patchValue({
        starts_at: starts ? starts.slice(0, 10) : starts,
        ends_at: ends ? ends.slice(0, 10) : '',
      });
    }
  }

  submit(): void {
    if (this.form.invalid) return;
    this.saving = true;
    this.error = '';
    const raw = this.form.getRawValue();
    const isBirthday = raw.event_kind === 'birthday';
    const useDate = raw.all_day || isBirthday;
    let endsRaw = raw.ends_at;
    if (isBirthday && raw.all_day && !endsRaw) {
      endsRaw = raw.starts_at.slice(0, 10);
    }
    const payload = {
      title: raw.title,
      category: raw.category,
      recurrence: isBirthday ? ('yearly' as EventRecurrence) : raw.recurrence,
      event_kind: raw.event_kind,
      starts_at: useDate
        ? new Date(raw.starts_at.slice(0, 10) + 'T00:00:00').toISOString()
        : new Date(raw.starts_at).toISOString(),
      ends_at: endsRaw
        ? useDate
          ? new Date(endsRaw.slice(0, 10) + 'T23:59:59').toISOString()
          : new Date(endsRaw).toISOString()
        : null,
      all_day: raw.all_day,
      location: raw.location || null,
      description: raw.description || null,
    };

    const req =
      this.isEdit && this.eventId
        ? this.calendarService.update(this.eventId, payload)
        : this.calendarService.create(payload);

    req.subscribe({
      next: (event) => this.router.navigate(['/calendar', event.id]),
      error: (err) => {
        this.error = err?.error?.detail || 'Failed to save event';
        this.saving = false;
      },
    });
  }
}
