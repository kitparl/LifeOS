import { Component, Input, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DashboardService } from '../services/dashboard.service';
import { HabitTodayItem } from '../models/dashboard.models';
import { HabitsService } from '../../habits/services/habits.service';
import { WidgetSkeletonComponent } from './widget-skeleton.component';

@Component({
  selector: 'app-habits-widget',
  standalone: true,
  imports: [WidgetSkeletonComponent, RouterLink],
  template: `
    <div class="panel !p-0 overflow-hidden h-full">
      <div class="title-bar rounded-none border-x-0 border-t-0 flex items-center justify-between pr-2">
        <span>Today's Habits</span>
        <a routerLink="/habits" class="text-[10px] font-normal underline">All</a>
      </div>
      @if (loading) {
        <app-widget-skeleton />
      } @else if (habits.length === 0) {
        <p class="p-3 text-sm text-gray-600">
          No habits tracked yet.
          <a routerLink="/habits/new" class="text-[var(--xp-blue)] underline">Add one</a>
        </p>
      } @else {
        <ul class="divide-y divide-[var(--xp-border)] text-sm">
          @for (habit of habits; track habit.id) {
            <li class="flex items-center gap-2 px-3 py-2">
              <input
                type="checkbox"
                [checked]="habit.completed"
                (change)="toggle(habit, $event)"
              />
              <a [routerLink]="['/habits', habit.id]" class="hover:underline" [class.line-through]="habit.completed">
                {{ habit.name }}
              </a>
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class HabitsWidgetComponent {
  private readonly habitsService = inject(HabitsService);
  private readonly dashboard = inject(DashboardService);

  @Input() loading = false;
  @Input() habits: HabitTodayItem[] = [];

  toggle(habit: HabitTodayItem, event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    const req = checked
      ? this.habitsService.completeToday(habit.id)
      : this.habitsService.uncompleteToday(habit.id);
    req.subscribe({
      next: () => this.dashboard.getSummary().subscribe(),
      error: () => this.dashboard.getSummary().subscribe(),
    });
  }
}
