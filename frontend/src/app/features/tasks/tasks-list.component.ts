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
    <div class="space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 class="text-xl font-semibold sm:text-2xl">Tasks</h1>
          <p class="text-sm text-[var(--text-muted)]">Track priorities, deadlines, and subtasks.</p>
        </div>
        <a routerLink="/tasks/new" class="btn-primary text-xs no-underline sm:text-sm">New Task</a>
      </div>

      <form class="grid gap-3 text-sm sm:grid-cols-2 xl:grid-cols-[minmax(0,1.5fr)_repeat(3,minmax(0,1fr))]" [formGroup]="filters" (ngSubmit)="load()">
        <input class="input-field min-w-0" formControlName="search" placeholder="Search…" />
        <select class="input-field min-w-0" formControlName="status">
          <option value="">All statuses</option>
          @for (s of statuses; track s.value) {
            <option [value]="s.value">{{ s.label }}</option>
          }
        </select>
        <select class="input-field min-w-0" formControlName="priority">
          <option value="">All priorities</option>
          @for (p of priorities; track p.value) {
            <option [value]="p.value">{{ p.label }}</option>
          }
        </select>
        <label class="flex min-h-11 items-center gap-2 rounded-xl border border-[var(--xp-border)] bg-[var(--surface)] px-3 text-xs text-[var(--text-muted)]">
          <input type="checkbox" formControlName="due_today" />
          Due today
        </label>
        <button type="submit" class="btn-primary text-xs sm:col-span-2 xl:col-span-1">Filter</button>
      </form>

      @if (loading) {
        <p class="text-sm text-gray-600">Loading tasks…</p>
      } @else if (tasks.length === 0) {
        <div class="panel">
          <p class="text-sm text-gray-600">No tasks found.</p>
          <a routerLink="/tasks/new" class="btn-primary mt-2 inline-block text-xs no-underline">Create task</a>
        </div>
      } @else {
        <div class="space-y-3 md:hidden">
          @for (task of tasks; track task.id) {
            <article class="panel space-y-3">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <a [routerLink]="['/tasks', task.id]" class="block truncate text-base font-semibold text-[var(--xp-blue)] underline">
                    {{ task.title }}
                  </a>
                  <p class="mt-1 text-xs capitalize text-[var(--text-muted)]">
                    {{ task.priority }} priority · {{ task.status.replace('_', ' ') }}
                  </p>
                </div>
                @if (task.status !== 'completed') {
                  <button type="button" class="btn-primary px-3 text-xs" (click)="complete(task.id)">Done</button>
                }
              </div>
              <div class="grid grid-cols-2 gap-3 text-xs text-[var(--text-muted)]">
                <div>
                  <p class="font-medium text-[var(--xp-text)]">Due</p>
                  <p>{{ task.due_date ? (task.due_date | date: 'mediumDate') : '—' }}</p>
                </div>
                <div>
                  <p class="font-medium text-[var(--xp-text)]">Subtasks</p>
                  <p>{{ task.completed_subtasks }}/{{ task.subtask_count }}</p>
                </div>
              </div>
            </article>
          }
        </div>
        <div class="panel hidden !p-0 overflow-hidden md:block">
          <table class="w-full text-sm">
            <thead class="border-b border-[var(--xp-border)] bg-[var(--xp-silver)] text-left">
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
                <tr class="border-b border-[var(--xp-border)] hover:bg-[var(--primary-soft)]">
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
