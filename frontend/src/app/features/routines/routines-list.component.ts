import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ConfirmService } from '../../shared/confirm/confirm.service';
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
        <div class="space-y-2 md:hidden">
          @for (r of routines; track r.id) {
            <article class="panel space-y-2">
              <a [routerLink]="['/routines', r.id]" class="link font-medium">{{ r.name }}</a>
              <p class="text-xs" style="color: var(--text-muted)">
                {{ daysLabel(r.days_of_week) }} · {{ r.block_count }} blocks · {{ r.is_active ? 'Active' : 'Paused' }}
              </p>
              <p class="text-xs" style="color: var(--text-muted)">
                @if (r.start_date || r.end_date) {
                  {{ r.start_date || '…' }} → {{ r.end_date || '…' }}
                } @else {
                  —
                }
              </p>
              <div class="flex flex-wrap gap-2">
                <a [routerLink]="['/routines', r.id, 'edit']" class="btn-ghost text-xs no-underline">Edit</a>
                @if (r.is_active) {
                  <button type="button" class="btn-ghost text-xs" (click)="deactivate(r)">Deactivate</button>
                } @else {
                  <button type="button" class="btn-ghost text-xs" (click)="activate(r)">Activate</button>
                }
                <button type="button" class="btn-ghost text-xs" style="color: var(--danger)" (click)="remove(r)">Delete</button>
              </div>
            </article>
          }
        </div>
        <div class="panel hidden !p-0 overflow-hidden md:block">
          <table class="w-full text-sm">
            <thead class="border-b border-[var(--xp-border)] bg-[var(--surface-2)] text-left">
              <tr>
                <th class="px-3 py-2">Name</th>
                <th class="px-3 py-2">Days</th>
                <th class="px-3 py-2">Period</th>
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
                  <td class="px-3 py-2 text-xs" style="color: var(--text-muted)">
                    @if (r.start_date || r.end_date) {
                      {{ r.start_date || '…' }} → {{ r.end_date || '…' }}
                    } @else {
                      —
                    }
                  </td>
                  <td class="px-3 py-2">{{ r.block_count }}</td>
                  <td class="px-3 py-2">{{ r.is_active ? 'Active' : 'Paused' }}</td>
                  <td class="px-3 py-2">
                    <div class="flex flex-wrap gap-2">
                      <a [routerLink]="['/routines', r.id, 'edit']" class="text-xs underline">Edit</a>
                      @if (r.is_active) {
                        <button type="button" class="text-xs underline" (click)="deactivate(r)">Deactivate</button>
                      } @else {
                        <button type="button" class="text-xs underline" (click)="activate(r)">Activate</button>
                      }
                      <button type="button" class="text-xs underline" style="color: var(--danger)" (click)="remove(r)">Delete</button>
                    </div>
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
  private readonly confirm = inject(ConfirmService);

  routines: RoutineListItem[] = [];
  loading = false;

  filters = this.fb.nonNullable.group({ active_only: true });

  ngOnInit(): void {
    this.filters.controls.active_only.valueChanges.subscribe(() => this.load());
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

  deactivate(routine: RoutineListItem): void {
    this.routinesService.update(routine.id, { is_active: false }).subscribe({ next: () => this.load() });
  }

  activate(routine: RoutineListItem): void {
    this.routinesService.update(routine.id, { is_active: true }).subscribe({ next: () => this.load() });
  }

  async remove(routine: RoutineListItem): Promise<void> {
    const ok = await this.confirm.confirm(`Delete routine "${routine.name}" permanently?`);
    if (!ok) return;
    this.routinesService.delete(routine.id).subscribe({ next: () => this.load() });
  }
}
