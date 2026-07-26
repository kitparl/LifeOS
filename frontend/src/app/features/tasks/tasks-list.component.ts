import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ListPaginatorComponent } from '../../shared/pagination/list-paginator.component';
import { TASK_PRIORITIES, TASK_STATUSES, TaskListItem, TaskScope } from './models/task.models';
import { TasksService } from './services/tasks.service';

@Component({
  selector: 'app-tasks-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe, ListPaginatorComponent],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Tasks</h1>
        <a routerLink="/tasks/new" class="btn-primary text-xs no-underline">New Task</a>
      </div>

      <div class="flex flex-wrap gap-1.5 text-xs">
        @for (tab of scopeTabs; track tab.value) {
          <button
            type="button"
            class="rounded-lg border px-3 py-1.5"
            [class.bg-[var(--primary-soft)]]="scope === tab.value"
            [style.border-color]="'var(--xp-border)'"
            (click)="setScope(tab.value)"
          >
            {{ tab.label }}
          </button>
        }
      </div>

      <form class="flex flex-wrap gap-2 text-sm" [formGroup]="filters" (ngSubmit)="applyFilters()">
        <input class="input-field !w-auto min-w-[10rem] flex-1" formControlName="search" placeholder="Search…" />
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
        <label class="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
          <input type="checkbox" formControlName="due_today" />
          Due today
        </label>
        <button type="submit" class="btn-primary text-xs">Filter</button>
      </form>

      @if (loading) {
        <p class="text-sm" style="color: var(--text-muted)">Loading tasks…</p>
      } @else if (tasks.length === 0) {
        <div class="panel">
          <p class="text-sm" style="color: var(--text-muted)">
            {{
              scope === 'assigned_to_me'
                ? 'No tasks from others assigned to you.'
                : 'No tasks yet.'
            }}
          </p>
          @if (scope === 'owned') {
            <a routerLink="/tasks/new" class="btn-primary mt-2 inline-block text-xs no-underline">Create task</a>
          }
        </div>
      } @else {
        <div class="space-y-2 md:hidden">
          @for (task of pagedTasks; track task.id) {
            <article class="panel space-y-2 !py-3">
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <a [routerLink]="['/tasks', task.id]" class="link font-medium">{{ task.title }}</a>
                  <div class="mt-1.5 flex flex-wrap gap-1">
                    <span class="chip text-xs capitalize">{{ task.priority }}</span>
                    <span class="chip text-xs capitalize">{{ task.status.replace('_', ' ') }}</span>
                    @if (task.assignment_status === 'pending') {
                      <span class="chip text-xs" style="color: var(--warning, #b45309)">Pending accept</span>
                    }
                  </div>
                  <p class="mt-1 text-xs" style="color: var(--text-muted)">
                    {{ task.due_date ? (task.due_date | date: 'mediumDate') : 'No due date' }}
                    · {{ task.completed_subtasks }}/{{ task.subtask_count }} subtasks
                  </p>
                </div>
                @if (task.status !== 'completed') {
                  <button type="button" class="btn-primary shrink-0 px-2 text-xs" (click)="complete(task.id)">
                    Done
                  </button>
                }
              </div>
            </article>
          }
          <app-list-paginator
            [total]="tasks.length"
            [pageSize]="pageSize"
            [currentPage]="currentPage"
            (pageChange)="setPage($event)"
          />
        </div>

        <div class="panel hidden !p-0 overflow-hidden md:block">
          <table class="w-full text-sm">
            <thead class="border-b border-[var(--xp-border)] bg-[var(--xp-silver)] text-left text-xs">
              <tr>
                <th class="px-3 py-2 font-medium">Title</th>
                <th class="px-3 py-2 font-medium">Priority</th>
                <th class="px-3 py-2 font-medium">Status</th>
                <th class="px-3 py-2 font-medium">Due</th>
                <th class="px-3 py-2 font-medium">Subtasks</th>
                <th class="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              @for (task of pagedTasks; track task.id) {
                <tr class="border-b border-[var(--xp-border)] hover:bg-[var(--primary-soft)]">
                  <td class="px-3 py-2">
                    <a [routerLink]="['/tasks', task.id]" class="link font-medium">{{ task.title }}</a>
                    @if (task.assignment_status === 'pending') {
                      <span class="chip ml-2 text-xs" style="color: var(--warning, #b45309)">Pending</span>
                    }
                  </td>
                  <td class="px-3 py-2 capitalize text-xs">{{ task.priority }}</td>
                  <td class="px-3 py-2">
                    <span class="chip text-xs capitalize">{{ task.status.replace('_', ' ') }}</span>
                  </td>
                  <td class="px-3 py-2 text-xs" style="color: var(--text-muted)">
                    {{ task.due_date ? (task.due_date | date: 'mediumDate') : '—' }}
                  </td>
                  <td class="px-3 py-2 text-xs">{{ task.completed_subtasks }}/{{ task.subtask_count }}</td>
                  <td class="px-3 py-2 text-right">
                    @if (task.status !== 'completed') {
                      <button type="button" class="btn-ghost text-xs" (click)="complete(task.id)">Done</button>
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
          <app-list-paginator
            [total]="tasks.length"
            [pageSize]="pageSize"
            [currentPage]="currentPage"
            (pageChange)="setPage($event)"
          />
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
  scopeTabs: { value: TaskScope; label: string }[] = [
    { value: 'owned', label: 'My tasks' },
    { value: 'assigned_to_me', label: 'Assigned to me' },
  ];
  tasks: TaskListItem[] = [];
  loading = false;
  currentPage = 1;
  scope: TaskScope = 'owned';
  readonly pageSize = 12;

  filters = this.fb.nonNullable.group({
    search: '',
    status: '',
    priority: '',
    due_today: false,
  });

  ngOnInit(): void {
    this.load();
  }

  get pagedTasks(): TaskListItem[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.tasks.slice(start, start + this.pageSize);
  }

  setScope(scope: TaskScope): void {
    this.scope = scope;
    this.currentPage = 1;
    this.load();
  }

  applyFilters(): void {
    this.currentPage = 1;
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
        scope: this.scope,
      })
      .subscribe({
        next: (data) => {
          this.tasks = data;
          this.clampPage();
          this.loading = false;
        },
        error: () => (this.loading = false),
      });
  }

  complete(id: string): void {
    this.tasksService.complete(id).subscribe({ next: () => this.load() });
  }

  setPage(page: number): void {
    this.currentPage = page;
  }

  private clampPage(): void {
    const totalPages = Math.max(1, Math.ceil(this.tasks.length / this.pageSize));
    this.currentPage = Math.min(this.currentPage, totalPages);
  }
}
