import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ConfirmService } from '../../shared/confirm/confirm.service';
import { HABIT_FREQUENCIES, HabitListItem } from './models/habit.models';
import { HabitsService } from './services/habits.service';

@Component({
  selector: 'app-habits-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Habits</h1>
        <a routerLink="/habits/new" class="btn-primary text-xs no-underline">New Habit</a>
      </div>

      <form class="flex flex-wrap gap-2 text-sm" [formGroup]="filters" (ngSubmit)="load()">
        <label class="flex items-center gap-1 text-xs">
          <input type="checkbox" formControlName="active_only" />
          Active only
        </label>
        <button type="submit" class="btn-primary text-xs">Refresh</button>
      </form>

      @if (loading) {
        <p class="text-sm" style="color: var(--text-muted)">Loading habits…</p>
      } @else if (habits.length === 0) {
        <div class="panel">
          <p class="text-sm" style="color: var(--text-muted)">No habits yet.</p>
          <a routerLink="/habits/new" class="btn-primary mt-2 inline-block text-xs no-underline">Create habit</a>
        </div>
      } @else {
        <div class="space-y-2 md:hidden">
          @for (habit of habits; track habit.id) {
            <article class="panel space-y-2">
              <div class="flex items-start gap-2">
                <input
                  type="checkbox"
                  class="mt-1"
                  [checked]="habit.completed_today"
                  (change)="toggleToday(habit, $event)"
                />
                <div class="min-w-0 flex-1">
                  <a [routerLink]="['/habits', habit.id]" class="link font-medium">{{ habit.name }}</a>
                  <p class="text-xs capitalize" style="color: var(--text-muted)">
                    {{ habit.frequency }} · streak {{ habit.streak }} · {{ habit.completion_rate }}%
                  </p>
                </div>
              </div>
              <div class="flex flex-wrap gap-2">
                <a [routerLink]="['/habits', habit.id, 'edit']" class="btn-ghost text-xs no-underline">Edit</a>
                <button type="button" class="btn-ghost text-xs" style="color: var(--danger)" (click)="remove(habit)">Delete</button>
              </div>
            </article>
          }
        </div>
        <div class="panel hidden !p-0 overflow-hidden md:block">
          <table class="w-full text-sm">
            <thead class="border-b border-[var(--xp-border)] bg-[var(--surface-2)] text-left">
              <tr>
                <th class="px-3 py-2 w-10">Today</th>
                <th class="px-3 py-2">Name</th>
                <th class="px-3 py-2">Frequency</th>
                <th class="px-3 py-2">Streak</th>
                <th class="px-3 py-2">Rate</th>
                <th class="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              @for (habit of habits; track habit.id) {
                <tr class="border-b border-[var(--xp-border)] hover:bg-[var(--surface-2)]">
                  <td class="px-3 py-2">
                    <input
                      type="checkbox"
                      [checked]="habit.completed_today"
                      (change)="toggleToday(habit, $event)"
                    />
                  </td>
                  <td class="px-3 py-2">
                    <a [routerLink]="['/habits', habit.id]" class="link">{{ habit.name }}</a>
                  </td>
                  <td class="px-3 py-2 capitalize">{{ habit.frequency }}</td>
                  <td class="px-3 py-2">{{ habit.streak }}</td>
                  <td class="px-3 py-2">{{ habit.completion_rate }}%</td>
                  <td class="px-3 py-2">
                    <div class="flex flex-wrap gap-2">
                      <a [routerLink]="['/habits', habit.id, 'edit']" class="text-xs underline">Edit</a>
                      <button type="button" class="text-xs underline" style="color: var(--danger)" (click)="remove(habit)">Delete</button>
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
export class HabitsListComponent implements OnInit {
  private readonly habitsService = inject(HabitsService);
  private readonly fb = inject(FormBuilder);
  private readonly confirm = inject(ConfirmService);

  frequencies = HABIT_FREQUENCIES;
  habits: HabitListItem[] = [];
  loading = false;

  filters = this.fb.nonNullable.group({ active_only: true });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    const activeOnly = this.filters.getRawValue().active_only;
    this.habitsService.list(activeOnly).subscribe({
      next: (data) => {
        this.habits = data;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }

  toggleToday(habit: HabitListItem, event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    const req = checked
      ? this.habitsService.completeToday(habit.id)
      : this.habitsService.uncompleteToday(habit.id);
    req.subscribe({
      next: () => this.load(),
      error: () => this.load(),
    });
  }

  async remove(habit: HabitListItem): Promise<void> {
    const ok = await this.confirm.confirm(`Delete habit "${habit.name}" permanently?`);
    if (!ok) return;
    this.habitsService.delete(habit.id).subscribe({ next: () => this.load() });
  }
}
