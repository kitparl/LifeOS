import { DatePipe } from '@angular/common';
import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TaskTodayItem } from '../models/dashboard.models';
import { WidgetSkeletonComponent } from './widget-skeleton.component';

@Component({
  selector: 'app-tasks-widget',
  standalone: true,
  imports: [DatePipe, RouterLink, WidgetSkeletonComponent],
  template: `
    <div class="panel !p-0 overflow-hidden h-full">
      <div class="title-bar rounded-none border-x-0 border-t-0 flex justify-between">
        <span>Today's Tasks</span>
        <a routerLink="/tasks" class="text-xs font-normal underline opacity-90">View all</a>
      </div>
      @if (loading) {
        <app-widget-skeleton />
      } @else if (tasks.length === 0) {
        <div class="p-3 text-sm text-gray-600">
          <p>No tasks today</p>
          <a routerLink="/tasks/new" class="btn-primary mt-2 inline-block text-xs no-underline">Add task</a>
        </div>
      } @else {
        <ul class="divide-y divide-[var(--xp-border)] text-sm">
          @for (task of tasks; track task.id) {
            <li class="flex justify-between gap-2 px-3 py-2">
              <a [routerLink]="['/tasks', task.id]" class="no-underline text-inherit hover:underline">{{ task.title }}</a>
              @if (task.due_at) {
                <span class="text-xs text-gray-500 shrink-0">{{ task.due_at | date: 'shortTime' }}</span>
              }
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class TasksWidgetComponent {
  @Input() loading = false;
  @Input() tasks: TaskTodayItem[] = [];
}
