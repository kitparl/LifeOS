import { Component, EventEmitter, Input, Output } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { CalendarEvent, categoryColor } from './models/calendar.models';

/** Read-only event summary opened by clicking an event on the calendar. */
@Component({
  selector: 'app-calendar-event-modal',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <div class="modal-backdrop" (click)="closed.emit()">
      <div class="modal" (click)="$event.stopPropagation()" style="max-width: 440px">
        <div class="modal-header" style="gap: 0.5rem">
          <span
            class="inline-block w-3 h-3 rounded-full shrink-0"
            [style.background]="categoryColor(event.category)"
          ></span>
          <span class="flex-1 truncate">{{ event.title }}</span>
          <button type="button" class="btn-ghost !px-2 text-xs" (click)="closed.emit()">✕</button>
        </div>
        <div class="modal-body space-y-3 text-sm">
          <!-- Date / time -->
          <div class="flex items-start gap-2" style="color: var(--text-muted)">
            <span>📅</span>
            <span>
              @if (event.all_day) {
                {{ event.starts_at | date: 'EEEE, MMMM d, y' }}
                @if (event.ends_at) {
                  &nbsp;– {{ event.ends_at! | date: 'EEEE, MMMM d, y' }}
                }
              } @else {
                {{ event.starts_at | date: 'EEE, MMM d · h:mm a' }}
                @if (event.ends_at) {
                  &nbsp;– {{ event.ends_at! | date: 'h:mm a' }}
                }
              }
            </span>
          </div>

          <!-- Category -->
          <div class="flex items-center gap-2">
            <span
              class="inline-block px-2 py-0.5 rounded-full text-xs font-medium text-white capitalize"
              [style.background]="categoryColor(event.category)"
            >
              {{ event.category }}
            </span>
            @if (event.recurrence !== 'none') {
              <span class="text-xs" style="color: var(--text-muted)">
                🔁 {{ event.recurrence }}
              </span>
            }
            @if (event.source_module === 'google_calendar') {
              <span class="qa-type-badge">Google</span>
            }
          </div>

          <!-- Location -->
          @if (event.location) {
            <div class="flex items-start gap-2" style="color: var(--text-muted)">
              <span>📍</span>
              <span>{{ event.location }}</span>
            </div>
          }

          <!-- Description -->
          @if (event.description) {
            <div class="flex items-start gap-2" style="color: var(--text)">
              <span style="color: var(--text-muted)">📝</span>
              <p class="whitespace-pre-wrap">{{ event.description }}</p>
            </div>
          }
        </div>
        <div class="modal-footer">
          @if (!event.read_only) {
            <button
              type="button"
              class="btn-ghost text-xs"
              style="color: var(--danger)"
              (click)="deleteRequested.emit(event.id)"
              [disabled]="deleting"
            >
              {{ deleting ? 'Deleting…' : 'Delete' }}
            </button>
          } @else {
            <span class="text-xs" style="color: var(--text-muted)">Synced from Google (read-only)</span>
          }
          <div class="flex-1"></div>
          @if (!event.read_only) {
            <a
              [routerLink]="['/calendar', event.id, 'edit']"
              class="btn-secondary text-xs no-underline"
              (click)="closed.emit()"
            >
              Edit
            </a>
          }
          <button type="button" class="btn-primary text-xs" (click)="closed.emit()">Done</button>
        </div>
      </div>
    </div>
  `,
})
export class CalendarEventModalComponent {
  @Input({ required: true }) event!: CalendarEvent;
  @Input() deleting = false;
  @Output() readonly closed = new EventEmitter<void>();
  @Output() readonly deleteRequested = new EventEmitter<string>();

  readonly categoryColor = categoryColor;
}
