import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { TASK_PRIORITIES, TASK_STATUSES, TaskListItem } from './models/task.models';
import { TasksService } from './services/tasks.service';

@Component({
  selector: 'app-tasks-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Tasks</h1>
        <a routerLink="/tasks/new" class="btn-primary text-xs no-underline">New Task</a>
      </div>

      <form class="flex flex-wrap gap-2 text-sm" [formGroup]="filters" (ngSubmit)="load()">
        <input class="input-field !w-40" formControlName="search" placeholder="Search…" />
        <select class="input-field !w-auto" formControlName="status">
          <option value="">All statuses</option>
          @for (s of statuses; track s.value) {
            <option [value]="s.value">{{ s.label }}</option>
          }
        </select>
        <select class="input-field !w-auto" formControlName="priority">
          <option value="">All priorities</option>
          @for (p of priorities; track p.value) {
            <option [value]="p.value">{{ p.label }}</option>
          }
        </select>
        <label class="flex items-center gap-1 text-xs">
          <input type="checkbox" formControlName="due_today" />
          Due today
        </label>
        <button type="submit" class="btn-primary text-xs">Filter</button>
      </form>

      @if (loading) {
        <p class="text-sm text-gray-600">Loading tasks…</p>
      } @else if (tasks.length === 0) {
        <div class="panel">
          <p class="text-sm text-gray-600">No tasks found.</p>
          <a routerLink="/tasks/new" class="btn-primary mt-2 inline-block text-xs no-underline">Create task</a>
        </div>
      } @else {
        <div class="panel !p-0 overflow-hidden">
          <table class="w-full text-sm">
            <thead class="border-b border-[var(--xp-border)] bg-[#e8e8e8] text-left">
              <tr>
                <th class="px-3 py-2">Title</th>
                <th class="px-3 py-2">Priority</th>
                <th class="px-3 py-2">Status</th>
                <th class="px-3 py-2">Due</th>
                <th class="px-3 py-2">Subtasks</th>
                <th class="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              @for (task of tasks; track task.id) {
                <tr class="border-b border-[var(--xp-border)] hover:bg-[#d6e4f7]">
                  <td class="px-3 py-2">
                    <a [routerLink]="['/tasks', task.id]" class="text-[var(--xp-blue)] underline">{{ task.title }}</a>
                  </td>
                  <td class="px-3 py-2 capitalize">{{ task.priority }}</td>
                  <td class="px-3 py-2 capitalize">{{ task.status.replace('_', ' ') }}</td>
                  <td class="px-3 py-2 text-xs text-gray-600">
                    {{ task.due_date ? (task.due_date | date: 'mediumDate') : '—' }}
                  </td>
                  <td class="px-3 py-2 text-xs">{{ task.completed_subtasks }}/{{ task.subtask_count }}</td>
                  <td class="px-3 py-2">
                    @if (task.status !== 'completed') {
                      <button type="button" class="text-xs text-green-700 underline" (click)="complete(task.id)">Done</button>
                    }
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
export class TasksListComponent implements OnInit {
  private readonly tasksService = inject(TasksService);
  private readonly fb = inject(FormBuilder);

  priorities = TASK_PRIORITIES;
  statuses = TASK_STATUSES;
  tasks: TaskListItem[] = [];
  loading = false;

  filters = this.fb.nonNullable.group({
    search: '',
    status: '',
    priority: '',
    due_today: false,
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    const raw = this.filters.getRawValue();
    this.tasksService
      .list({
        search: raw.search || undefined,
        status: raw.status || undefined,
        priority: raw.priority || undefined,
        due_today: raw.due_today || undefined,
      })
      .subscribe({
        next: (data) => {
          this.tasks = data;
          this.loading = false;
        },
        error: () => (this.loading = false),
      });
  }

  complete(id: string): void {
    this.tasksService.complete(id).subscribe({ next: () => this.load() });
  }
}
