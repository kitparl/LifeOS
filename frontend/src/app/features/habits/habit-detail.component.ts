import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { Habit } from './models/habit.models';
import { HabitsService } from './services/habits.service';

interface HeatmapDay {
  date: string;
  completed: boolean;
}

@Component({
  selector: 'app-habit-detail',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    @if (habit; as h) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 class="text-lg font-semibold">{{ h.name }}</h1>
            <p class="text-xs capitalize text-gray-600">{{ h.frequency }} · {{ h.is_active ? 'active' : 'inactive' }}</p>
          </div>
          <div class="flex gap-2">
            <button
              type="button"
              class="btn-primary text-xs"
              (click)="toggleToday()"
            >
              {{ h.completed_today ? 'Undo today' : 'Complete today' }}
            </button>
            <a [routerLink]="['/habits', h.id, 'edit']" class="btn-primary text-xs no-underline">Edit</a>
            <button type="button" class="input-field !w-auto text-xs text-red-700" (click)="remove()">Delete</button>
          </div>
        </div>

        @if (h.description) {
          <div class="panel text-sm">
            <p class="whitespace-pre-wrap text-gray-700">{{ h.description }}</p>
          </div>
        }

        <div class="grid gap-3 md:grid-cols-3">
          <div class="panel text-sm">
            <p class="text-xs text-gray-600">Current streak</p>
            <p class="text-2xl font-semibold">{{ h.streak }}</p>
          </div>
          <div class="panel text-sm">
            <p class="text-xs text-gray-600">30-day completion</p>
            <p class="text-2xl font-semibold">{{ h.completion_rate }}%</p>
          </div>
          <div class="panel text-sm">
            <p class="text-xs text-gray-600">Total logs</p>
            <p class="text-2xl font-semibold">{{ h.stats.total_logs }}</p>
          </div>
        </div>

        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Activity (last 90 days)</div>
          <div class="p-3">
            <div class="flex flex-wrap gap-1">
              @for (day of heatmap; track day.date) {
                <span
                  class="h-3 w-3 border border-[var(--xp-border)]"
                  [class.bg-green-600]="day.completed"
                  [class.bg-gray-200]="!day.completed"
                  [title]="day.date"
                ></span>
              }
            </div>
            <p class="mt-2 text-xs text-gray-600">Darker green = completed</p>
          </div>
        </div>

        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Recent logs</div>
          @if (h.logs.length === 0) {
            <p class="p-3 text-sm text-gray-600">No logs yet.</p>
          } @else {
            <ul class="divide-y divide-[var(--xp-border)] text-sm">
              @for (log of h.logs; track log.id) {
                <li class="px-3 py-2">{{ log.log_date | date: 'mediumDate' }}</li>
              }
            </ul>
          }
        </div>

        <a routerLink="/habits" class="text-sm text-[var(--xp-blue)] underline">Back to habits</a>
      </div>
    } @else if (loading) {
      <p class="text-sm">Loading habit…</p>
    } @else {
      <p class="text-sm text-red-700">Habit not found.</p>
    }
  `,
})
export class HabitDetailComponent implements OnInit {
  private readonly habitsService = inject(HabitsService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  habit: Habit | null = null;
  loading = false;
  heatmap: HeatmapDay[] = [];

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) this.load(id);
  }

  load(id: string): void {
    this.loading = true;
    this.habitsService.get(id).subscribe({
      next: (h) => {
        this.habit = h;
        this.heatmap = this.buildHeatmap(h);
        this.loading = false;
      },
      error: () => {
        this.habit = null;
        this.loading = false;
      },
    });
  }

  toggleToday(): void {
    if (!this.habit) return;
    const req = this.habit.completed_today
      ? this.habitsService.uncompleteToday(this.habit.id)
      : this.habitsService.completeToday(this.habit.id);
    req.subscribe({ next: () => this.load(this.habit!.id) });
  }

  remove(): void {
    if (!this.habit || !confirm('Delete this habit permanently?')) return;
    this.habitsService.delete(this.habit.id).subscribe({
      next: () => this.router.navigate(['/habits']),
    });
  }

  private buildHeatmap(habit: Habit): HeatmapDay[] {
    const logDates = new Set(habit.logs.map((l) => l.log_date.slice(0, 10)));
    const days: HeatmapDay[] = [];
    const today = new Date();
    for (let i = 89; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      days.push({ date: key, completed: logDates.has(key) });
    }
    return days;
  }
}
