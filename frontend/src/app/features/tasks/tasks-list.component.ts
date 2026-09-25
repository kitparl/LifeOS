import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin, Observable, tap } from 'rxjs';
import { TaskListSectionComponent } from './task-list-section.component';
import { combineDueDate, localDateInputValue } from './task-due-date.util';
import { TaskListItem, TaskScope } from './models/task.models';
import { TasksService } from './services/tasks.service';

type TaskListKey = 'today' | 'overdue' | 'nodate' | 'upcoming';
/** Overdue is shown inside the Today view, so it has no view of its own. */
type TaskView = Exclude<TaskListKey, 'overdue'>;

const TASK_LIST_KEYS: TaskListKey[] = ['today', 'overdue', 'nodate', 'upcoming'];

const LIST_QUERIES: Record<TaskListKey, Record<string, boolean>> = {
  today: { due_today: true, incomplete_only: true },
  overdue: { overdue: true },
  nodate: { has_due_date: false },
  upcoming: { due_later: true },
};

interface TaskListState {
  items: TaskListItem[];
  total: number;
  page: number;
  loading: boolean;
  error: boolean;
}

@Component({
  selector: 'app-tasks-list',
  standalone: true,
  imports: [ReactiveFormsModule, FormsModule, RouterLink, TaskListSectionComponent],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div class="flex gap-1 text-xs" role="group" aria-label="Whose tasks">
          @for (tab of scopeTabs; track tab.value) {
            <button
              type="button"
              class="rounded-lg border px-3 py-1.5"
              [class.bg-[var(--primary-soft)]]="scope === tab.value"
              [style.border-color]="'var(--xp-border)'"
              [attr.aria-pressed]="scope === tab.value"
              (click)="setScope(tab.value)"
            >
              {{ tab.label }}
            </button>
          }
        </div>
        <div class="flex items-center gap-3">
          @if (scope === 'owned') {
            <p class="text-xs" style="color: var(--text-muted)">
              {{ stats.completedToday }} done today
              @if (stats.streakDays > 0) {
                · {{ stats.streakDays }}-day streak
              }
            </p>
          }
          <a routerLink="/tasks/new" class="btn-secondary text-xs no-underline">New task</a>
        </div>
      </div>

      @if (scope === 'owned') {
        <form class="flex gap-2" (ngSubmit)="addQuickTask()">
          <label for="task-quick-add" class="sr-only">Quick add task</label>
          <input
            id="task-quick-add"
            class="input-field flex-1"
            [(ngModel)]="quickTitle"
            [ngModelOptions]="{ standalone: true }"
            placeholder="Add a task…"
            maxlength="200"
          />
          <button type="submit" class="btn-primary text-xs shrink-0" [disabled]="!quickTitle.trim() || quickAdding">
            Add
          </button>
        </form>
      }

      <div class="flex gap-1 text-xs" role="tablist" aria-label="Task views">
        @for (view of views; track view.key) {
          <button
            type="button"
            role="tab"
            class="flex-1 rounded-lg border px-2 py-1.5 md:flex-none md:px-3"
            [class.bg-[var(--primary-soft)]]="activeView === view.key"
            [class.font-medium]="activeView === view.key"
            [style.border-color]="'var(--xp-border)'"
            [attr.aria-selected]="activeView === view.key"
            (click)="setView(view.key)"
          >
            {{ view.label }} {{ lists[view.key].total }}
            @if (view.key === 'today' && lists.overdue.total > 0) {
              <span style="color: var(--warning)">· {{ lists.overdue.total }} overdue</span>
            }
          </button>
        }
      </div>

      @if (scheduleTaskId) {
        <div class="panel space-y-2 !py-3">
          <p class="text-sm font-medium">Due date for “{{ scheduleTaskTitle }}”</p>
          <div class="flex flex-wrap gap-2">
            <input
              class="input-field flex-1 min-w-[10rem]"
              type="date"
              aria-label="Due date"
              [(ngModel)]="scheduleDate"
              [ngModelOptions]="{ standalone: true }"
            />
            <input
              class="input-field !w-auto"
              type="time"
              aria-label="Time (optional)"
              [(ngModel)]="scheduleTime"
              [ngModelOptions]="{ standalone: true }"
            />
          </div>
          <div class="flex flex-wrap gap-2">
            <button type="button" class="btn-primary text-xs" [disabled]="!scheduleDate" (click)="confirmSchedule()">
              Save
            </button>
            <button type="button" class="btn-secondary text-xs" (click)="scheduleForToday(scheduleTaskId)">Today</button>
            <button type="button" class="btn-ghost text-xs" (click)="clearScheduleDate()">Remove date</button>
            <button type="button" class="btn-ghost text-xs" (click)="cancelSchedule()">Cancel</button>
          </div>
        </div>
      }

      @switch (activeView) {
        @case ('today') {
          <div class="space-y-4">
            @if (lists.overdue.total > 0 || lists.overdue.loading || lists.overdue.error) {
              <app-task-list-section
                title="Overdue"
                variant="overdue"
                [showTodayAction]="canSchedule"
                [showDateAction]="canSchedule"
                [tasks]="lists.overdue.items"
                [total]="lists.overdue.total"
                [pageSize]="pageSize"
                [currentPage]="lists.overdue.page"
                [loading]="lists.overdue.loading"
                [error]="lists.overdue.error"
                emptyMessage="Nothing overdue."
                (pageChange)="setPage('overdue', $event)"
                (retry)="loadList('overdue')"
                (complete)="complete($event)"
                (scheduleToday)="scheduleForToday($event)"
                (scheduleDate)="openSchedule($event)"
              />
            }
            <app-task-list-section
              title="Today"
              variant="today"
              [showHead]="lists.overdue.total > 0"
              [tasks]="lists.today.items"
              [total]="lists.today.total"
              [pageSize]="pageSize"
              [currentPage]="lists.today.page"
              [loading]="lists.today.loading"
              [error]="lists.today.error"
              [emptyMessage]="lists.overdue.total > 0 ? 'Nothing else due today.' : 'Nothing due today.'"
              (pageChange)="setPage('today', $event)"
              (retry)="loadList('today')"
              (complete)="complete($event)"
            >
              @if (lists.overdue.total === 0 && lists.nodate.total > 0) {
                <button emptyAction type="button" class="btn-secondary mt-2 text-xs" (click)="setView('nodate')">
                  Pick from No date ({{ lists.nodate.total }})
                </button>
              }
            </app-task-list-section>
          </div>
        }
        @case ('nodate') {
          <app-task-list-section
            title="No date"
            variant="nodate"
            [showHead]="false"
            [showTodayAction]="canSchedule"
            [showDateAction]="canSchedule"
            [tasks]="lists.nodate.items"
            [total]="lists.nodate.total"
            [pageSize]="pageSize"
            [currentPage]="lists.nodate.page"
            [loading]="lists.nodate.loading"
            [error]="lists.nodate.error"
            emptyMessage="No unscheduled tasks."
            (pageChange)="setPage('nodate', $event)"
            (retry)="loadList('nodate')"
            (complete)="complete($event)"
            (scheduleToday)="scheduleForToday($event)"
            (scheduleDate)="openSchedule($event)"
          >
            @if (scope === 'owned') {
              <a emptyAction routerLink="/tasks/new" class="btn-secondary mt-2 inline-block text-xs no-underline">
                Create task
              </a>
            }
          </app-task-list-section>
        }
        @case ('upcoming') {
          <app-task-list-section
            title="Upcoming"
            variant="upcoming"
            [showHead]="false"
            [showTodayAction]="canSchedule"
            [showDateAction]="canSchedule"
            [tasks]="lists.upcoming.items"
            [total]="lists.upcoming.total"
            [pageSize]="pageSize"
            [currentPage]="lists.upcoming.page"
            [loading]="lists.upcoming.loading"
            [error]="lists.upcoming.error"
            emptyMessage="Nothing scheduled ahead."
            (pageChange)="setPage('upcoming', $event)"
            (retry)="loadList('upcoming')"
            (complete)="complete($event)"
            (scheduleToday)="scheduleForToday($event)"
            (scheduleDate)="openSchedule($event)"
          />
        }
      }
    </div>
  `,
})
export class TasksListComponent implements OnInit {
  private readonly tasksService = inject(TasksService);
  private readonly fb = inject(FormBuilder);

  scopeTabs: { value: TaskScope; label: string }[] = [
    { value: 'owned', label: 'My tasks' },
    { value: 'assigned_to_me', label: 'Assigned to me' },
  ];
  views: { key: TaskView; label: string }[] = [
    { key: 'today', label: 'Today' },
    { key: 'nodate', label: 'No date' },
    { key: 'upcoming', label: 'Upcoming' },
  ];

  scope: TaskScope = 'owned';
  activeView: TaskView = 'today';
  readonly pageSize = 25;

  stats = { completedToday: 0, streakDays: 0 };
  quickTitle = '';
  quickAdding = false;
  scheduleTaskId: string | null = null;
  scheduleTaskTitle = '';
  scheduleDate = '';
  scheduleTime = '';

  lists: Record<TaskListKey, TaskListState> = {
    today: { items: [], total: 0, page: 1, loading: false, error: false },
    overdue: { items: [], total: 0, page: 1, loading: false, error: false },
    nodate: { items: [], total: 0, page: 1, loading: false, error: false },
    upcoming: { items: [], total: 0, page: 1, loading: false, error: false },
  };

  filters = this.fb.nonNullable.group({
    search: '',
    status: '',
    priority: '',
  });

  get canSchedule(): boolean {
    return this.scope === 'owned';
  }

  ngOnInit(): void {
    this.refresh();
  }

  setScope(scope: TaskScope): void {
    this.scope = scope;
    this.cancelSchedule();
    this.resetPages();
    this.refresh();
  }

  setView(view: TaskView): void {
    this.activeView = view;
  }

  setPage(key: TaskListKey, page: number): void {
    this.lists[key].page = page;
    this.loadList(key);
  }

  complete(id: string): void {
    this.tasksService.complete(id).subscribe({
      next: () => {
        if (this.scope === 'owned') {
          this.stats.completedToday += 1;
          if (this.stats.streakDays === 0) {
            this.stats.streakDays = 1;
          }
        }
        this.refresh(false);
      },
    });
  }

  scheduleForToday(id: string): void {
    const due = new Date();
    due.setHours(12, 0, 0, 0);
    this.tasksService.update(id, { due_date: due.toISOString() }).subscribe({
      next: () => {
        if (this.scheduleTaskId === id) {
          this.cancelSchedule();
        }
        this.refresh();
      },
    });
  }

  openSchedule(id: string): void {
    this.scheduleTaskId = id;
    this.scheduleTaskTitle = this.findTask(id)?.title ?? 'task';
    const d = new Date();
    d.setDate(d.getDate() + 1);
    this.scheduleDate = localDateInputValue(d);
    this.scheduleTime = '';
  }

  confirmSchedule(): void {
    if (!this.scheduleTaskId || !this.scheduleDate) {
      return;
    }
    const iso = combineDueDate(this.scheduleDate, this.scheduleTime);
    if (!iso) {
      return;
    }
    this.tasksService.update(this.scheduleTaskId, { due_date: iso }).subscribe({
      next: () => {
        this.cancelSchedule();
        this.refresh();
      },
    });
  }

  clearScheduleDate(): void {
    if (!this.scheduleTaskId) {
      return;
    }
    this.tasksService.update(this.scheduleTaskId, { due_date: null }).subscribe({
      next: () => {
        this.cancelSchedule();
        this.refresh();
      },
    });
  }

  cancelSchedule(): void {
    this.scheduleTaskId = null;
    this.scheduleTaskTitle = '';
    this.scheduleDate = '';
    this.scheduleTime = '';
  }

  addQuickTask(): void {
    const title = this.quickTitle.trim();
    if (!title || this.quickAdding) {
      return;
    }
    this.quickAdding = true;
    this.tasksService.create({ title }).subscribe({
      next: () => {
        this.quickTitle = '';
        this.quickAdding = false;
        this.activeView = 'nodate';
        this.refresh();
      },
      error: () => {
        this.quickAdding = false;
      },
    });
  }

  private refresh(reloadStats = true): void {
    const jobs: Observable<unknown>[] = TASK_LIST_KEYS.map((key) => this.fetchList(key));
    if (reloadStats && this.scope === 'owned') {
      jobs.push(
        this.tasksService.stats().pipe(
          tap((s) => {
            this.stats = { completedToday: s.completed_today, streakDays: s.streak_days };
          }),
        ),
      );
    }
    forkJoin(jobs).subscribe();
  }

  private resetPages(): void {
    TASK_LIST_KEYS.forEach((key) => {
      this.lists[key].page = 1;
    });
  }

  loadList(key: TaskListKey): void {
    this.fetchList(key).subscribe();
  }

  private findTask(id: string): TaskListItem | undefined {
    return TASK_LIST_KEYS.map((key) => this.lists[key].items.find((t) => t.id === id)).find(Boolean);
  }

  private fetchList(key: TaskListKey): Observable<unknown> {
    const state = this.lists[key];
    state.loading = true;
    state.error = false;
    const raw = this.filters.getRawValue();
    const offset = (state.page - 1) * this.pageSize;
    const viewQuery = { ...LIST_QUERIES[key] };

    if (!raw.status) {
      viewQuery['incomplete_only'] = true;
    }

    return this.tasksService
      .list({
        ...viewQuery,
        search: raw.search || undefined,
        status: raw.status || undefined,
        priority: raw.priority || undefined,
        scope: this.scope,
        limit: this.pageSize,
        offset,
      })
      .pipe(
        tap({
          next: (result) => {
            state.items = result.items;
            state.total = result.total;
            const totalPages = Math.max(1, Math.ceil(result.total / this.pageSize));
            if (state.page > totalPages) {
              state.page = totalPages;
            }
            state.loading = false;
          },
          error: () => {
            state.loading = false;
            state.error = true;
          },
        }),
      );
  }
}
