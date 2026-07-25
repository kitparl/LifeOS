import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { RoutineListItem, formatDaysLabel } from './models/routine.models';
import { RoutinesService } from './services/routines.service';

@Component({
  selector: 'app-routines-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 class="text-lg font-semibold">Routines</h1>
          <p class="text-xs" style="color: var(--text-muted)">
            Day schedules for DSA, gym, learning, books, and more — shown on Calendar.
          </p>
        </div>
        <a routerLink="/routines/new" class="btn-primary text-xs no-underline">New Routine</a>
      </div>

      <form class="flex flex-wrap gap-2 text-sm" [formGroup]="filters" (ngSubmit)="load()">
        <label class="flex items-center gap-1 text-xs">
          <input type="checkbox" formControlName="active_only" />
          Active only
        </label>
        <button type="submit" class="btn-primary text-xs">Refresh</button>
      </form>

      @if (loading) {
        <p class="text-sm" style="color: var(--text-muted)">Loading routines…</p>
      } @else if (routines.length === 0) {
        <div class="panel">
          <p class="text-sm" style="color: var(--text-muted)">
            No routines yet. Create a weekday schedule with timed blocks (DSA, gym, reading…).
          </p>
          <a routerLink="/routines/new" class="btn-primary mt-2 inline-block text-xs no-underline">
            Create routine
          </a>
        </div>
      } @else {
        <div class="panel !p-0 overflow-hidden">
          <table class="w-full text-sm">
            <thead class="border-b border-[var(--xp-border)] bg-[var(--surface-2)] text-left">
              <tr>
                <th class="px-3 py-2">Name</th>
                <th class="px-3 py-2">Days</th>
                <th class="px-3 py-2">Blocks</th>
                <th class="px-3 py-2">Status</th>
                <th class="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              @for (r of routines; track r.id) {
                <tr class="border-b border-[var(--xp-border)] hover:bg-[var(--surface-2)]">
                  <td class="px-3 py-2">
                    <a [routerLink]="['/routines', r.id]" class="link">{{ r.name }}</a>
                  </td>
                  <td class="px-3 py-2">{{ daysLabel(r.days_of_week) }}</td>
                  <td class="px-3 py-2">{{ r.block_count }}</td>
                  <td class="px-3 py-2">{{ r.is_active ? 'Active' : 'Paused' }}</td>
                  <td class="px-3 py-2">
                    <a [routerLink]="['/routines', r.id, 'edit']" class="text-xs underline">Edit</a>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `,
})
export class RoutinesListComponent implements OnInit {
  private readonly routinesService = inject(RoutinesService);
  private readonly fb = inject(FormBuilder);

  routines: RoutineListItem[] = [];
  loading = false;

  filters = this.fb.nonNullable.group({ active_only: false });

  ngOnInit(): void {
    this.load();
  }

  daysLabel(days: number[]): string {
    return formatDaysLabel(days);
  }

  load(): void {
    this.loading = true;
    const activeOnly = this.filters.getRawValue().active_only;
    this.routinesService.list(activeOnly).subscribe({
      next: (data) => {
        this.routines = data;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}
