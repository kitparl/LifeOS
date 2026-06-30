import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CalendarEvent } from './models/calendar.models';
import { CalendarService } from './services/calendar.service';

@Component({
  selector: 'app-event-detail',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    @if (event; as e) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 class="text-lg font-semibold">{{ e.title }}</h1>
            <p class="text-xs capitalize text-gray-600">{{ e.category }} · {{ e.recurrence }}</p>
          </div>
          <div class="flex gap-2">
            <a [routerLink]="['/calendar', e.id, 'edit']" class="btn-primary text-xs no-underline">Edit</a>
            <button type="button" class="input-field !w-auto text-xs text-red-700" (click)="remove()">Delete</button>
          </div>
        </div>

        <div class="panel text-sm space-y-2">
          <p><span class="font-medium">Starts:</span> {{ e.starts_at | date: 'full' }}</p>
          @if (e.ends_at) {
            <p><span class="font-medium">Ends:</span> {{ e.ends_at | date: 'full' }}</p>
          }
          @if (e.location) {
            <p><span class="font-medium">Location:</span> {{ e.location }}</p>
          }
          @if (e.description) {
            <p class="whitespace-pre-wrap text-gray-700">{{ e.description }}</p>
          }
        </div>

        <a routerLink="/calendar" class="text-sm text-[var(--xp-blue)] underline">Back to calendar</a>
      </div>
    } @else if (loading) {
      <p class="text-sm">Loading event…</p>
    } @else {
      <p class="text-sm text-red-700">Event not found.</p>
    }
  `,
})
export class EventDetailComponent implements OnInit {
  private readonly calendarService = inject(CalendarService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  event: CalendarEvent | null = null;
  loading = false;

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) this.load(id);
  }

  load(id: string): void {
    this.loading = true;
    this.calendarService.get(id).subscribe({
      next: (e) => {
        this.event = e;
        this.loading = false;
      },
      error: () => {
        this.event = null;
        this.loading = false;
      },
    });
  }

  remove(): void {
    if (!this.event || !confirm('Delete this event permanently?')) return;
    this.calendarService.delete(this.event.id).subscribe({
      next: () => this.router.navigate(['/calendar']),
    });
  }
}
