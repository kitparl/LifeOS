import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import {
  EVENT_CATEGORIES,
  EVENT_RECURRENCE,
  EventCategory,
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
            <label class="mb-1 block">Starts</label>
            <input class="input-field" type="datetime-local" formControlName="starts_at" />
          </div>
          <div>
            <label class="mb-1 block">Ends</label>
            <input class="input-field" type="datetime-local" formControlName="ends_at" />
          </div>
          <label class="flex items-center gap-2">
            <input type="checkbox" formControlName="all_day" />
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
            <p class="text-xs text-red-700">{{ error }}</p>
          }
          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">
              {{ saving ? 'Saving…' : 'Save' }}
            </button>
            <a routerLink="/calendar" class="input-field !w-auto inline-flex items-center no-underline text-gray-700">Cancel</a>
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
  isEdit = false;
  eventId: string | null = null;
  saving = false;
  error = '';

  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    category: ['personal' as EventCategory, Validators.required],
    recurrence: ['none' as EventRecurrence, Validators.required],
    starts_at: ['', Validators.required],
    ends_at: [''],
    all_day: [false],
    location: [''],
    description: [''],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.eventId = id;
      this.calendarService.get(id).subscribe({
        next: (event) => {
          this.form.patchValue({
            title: event.title,
            category: event.category,
            recurrence: event.recurrence,
            starts_at: event.starts_at.slice(0, 16),
            ends_at: event.ends_at ? event.ends_at.slice(0, 16) : '',
            all_day: event.all_day,
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

  submit(): void {
    if (this.form.invalid) return;
    this.saving = true;
    this.error = '';
    const raw = this.form.getRawValue();
    const payload = {
      title: raw.title,
      category: raw.category,
      recurrence: raw.recurrence,
      starts_at: new Date(raw.starts_at).toISOString(),
      ends_at: raw.ends_at ? new Date(raw.ends_at).toISOString() : null,
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
