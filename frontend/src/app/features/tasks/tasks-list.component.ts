import { NgTemplateOutlet } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin, Observable, tap } from 'rxjs';
import { TaskListSectionComponent } from './task-list-section.component';
import { combineDueDate, localDateInputValue } from './task-due-date.util';
import { TaskListItem, TaskScope } from './models/task.models';
import { TasksService } from './services/tasks.service';

type TaskListKey = 'today' | 'overdue' | 'nodate' | 'upcoming';
type TaskTab = 'today' | 'all';

interface ListViewConfig {
  key: TaskListKey;
  title: string;
  hint: string;
  emptyMessage: string;
  variant: 'today' | 'overdue' | 'nodate' | 'upcoming';
  query: Record<string, boolean>;
  showCreateLink?: boolean;
}

interface TaskListState {
  items: TaskListItem[];
  total: number;
  page: number;
  loading: boolean;
}

@Component({
  selector: 'app-tasks-list',
  standalone: true,
  imports: [NgTemplateOutlet, ReactiveFormsModule, FormsModule, RouterLink, TaskListSectionComponent],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h1 class="text-lg font-semibold">Tasks</h1>
          @if (scope === 'owned') {
            <p class="text-xs mt-0.5" style="color: var(--text-muted)">
              {{ stats.completedToday }} done today
              @if (stats.streakDays > 0) {
                · {{ stats.streakDays }}-day streak
              }
            </p>
          }
        </div>
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

      @if (scope === 'owned') {
        <form class="flex gap-2" (ngSubmit)="addQuickTask()">
          <input
            class="input-field flex-1"
            [(ngModel)]="quickTitle"
            [ngModelOptions]="{ standalone: true }"
            placeholder="Add a task (no date)…"
            maxlength="200"
          />
          <button type="submit" class="btn-primary text-xs shrink-0" [disabled]="!quickTitle.trim() || quickAdding">
            Add
          </button>
        </form>
      }

      <div class="flex flex-wrap gap-2 text-xs">
        @if (lists.today.total > 0) {
          <span class="chip">{{ lists.today.total }} today</span>
        }
        @if (lists.overdue.total > 0) {
          <span class="chip" style="color: var(--warning, #b45309)">{{ lists.overdue.total }} overdue</span>
        }
        @if (lists.nodate.total > 0) {
          <span class="chip">{{ lists.nodate.total }} no date</span>
        }
        @if (lists.upcoming.total > 0) {
          <span class="chip">{{ lists.upcoming.total }} upcoming</span>
        }
      </div>

      <div class="flex gap-1 text-xs md:hidden">
        @for (tab of viewTabs; track tab.id) {
          <button
            type="button"
            class="rounded-lg border px-3 py-1.5 flex-1"
            [class.bg-[var(--primary-soft)]]="activeTab === tab.id"
            [style.border-color]="'var(--xp-border)'"
            (click)="activeTab = tab.id"
          >
            {{ tab.label }}
            @if (tab.id === 'today') {
              ({{ lists.today.total }})
            } @else {
              ({{ allTasksTotal }})
            }
          </button>
        }
      </div>

      @if (scheduleTaskId) {
        <div class="panel space-y-2 !py-3">
          <p class="text-sm font-medium">Set due date</p>
          <div class="flex flex-wrap gap-2">
            <input class="input-field flex-1 min-w-[10rem]" type="date" [(ngModel)]="scheduleDate" [ngModelOptions]="{ standalone: true }" />
            <input class="input-field !w-auto" type="time" [(ngModel)]="scheduleTime" [ngModelOptions]="{ standalone: true }" aria-label="Time (optional)" />
          </div>
          <div class="flex flex-wrap gap-2">
            <button type="button" class="btn-primary text-xs" (click)="confirmSchedule()">Save</button>
            <button type="button" class="btn-ghost text-xs" (click)="clearScheduleDate()">Remove date</button>
            <button type="button" class="btn-ghost text-xs" (click)="cancelSchedule()">Cancel</button>
          </div>
        </div>
      }

      <div class="md:hidden">
        @if (activeTab === 'today') {
          <ng-container *ngTemplateOutlet="sectionToday" />
        } @else {
          <ng-container *ngTemplateOutlet="sectionAll" />
        }
      </div>

      <div class="hidden md:block space-y-4">
        <ng-container *ngTemplateOutlet="sectionToday" />
        <ng-container *ngTemplateOutlet="sectionAll" />
      </div>
    </div>

    <ng-template #sectionToday>
      <app-task-list-section
        title="Today"
        hint="Due today — tap Done or swipe right on mobile"
        variant="today"
        [tasks]="lists.today.items"
        [total]="lists.today.total"
        [pageSize]="pageSize"
        [currentPage]="lists.today.page"
        [loading]="lists.today.loading"
        emptyMessage="Nothing due today."
        (pageChange)="setPage('today', $event)"
        (complete)="complete($event)"
      />
    </ng-template>

    <ng-template #sectionAll>
      <div class="space-y-4">
        <p class="text-xs font-medium uppercase tracking-wide" style="color: var(--text-muted)">All other tasks</p>

        @if (lists.overdue.total > 0 || lists.overdue.loading) {
          <app-task-list-section
            title="Overdue"
            hint="Past due — tackle these first"
            variant="overdue"
            [showTodayAction]="canSchedule"
            [showDateAction]="canSchedule"
            [tasks]="lists.overdue.items"
            [total]="lists.overdue.total"
            [pageSize]="pageSize"
            [currentPage]="lists.overdue.page"
            [loading]="lists.overdue.loading"
            emptyMessage="Nothing overdue."
            (pageChange)="setPage('overdue', $event)"
            (complete)="complete($event)"
            (scheduleToday)="scheduleForToday($event)"
            (scheduleDate)="openSchedule($event)"
          />
        }

        <div class="grid gap-4 md:grid-cols-2">
          <app-task-list-section
            title="No date"
            hint="Not scheduled — add when ready"
            variant="nodate"
            [showTodayAction]="canSchedule"
            [showDateAction]="canSchedule"
            [tasks]="lists.nodate.items"
            [total]="lists.nodate.total"
            [pageSize]="pageSize"
            [currentPage]="lists.nodate.page"
            [loading]="lists.nodate.loading"
            [emptyMessage]="scope === 'assigned_to_me' ? 'No unscheduled tasks.' : 'No unscheduled tasks.'"
            [showCreateLink]="scope === 'owned'"
            (pageChange)="setPage('nodate', $event)"
            (complete)="complete($event)"
            (scheduleToday)="scheduleForToday($event)"
            (scheduleDate)="openSchedule($event)"
          />

          <app-task-list-section
            title="Upcoming"
            hint="Scheduled for future days"
            variant="upcoming"
            [showTodayAction]="canSchedule"
            [showDateAction]="canSchedule"
            [tasks]="lists.upcoming.items"
            [total]="lists.upcoming.total"
            [pageSize]="pageSize"
            [currentPage]="lists.upcoming.page"
            [loading]="lists.upcoming.loading"
            emptyMessage="Nothing scheduled ahead."
            (pageChange)="setPage('upcoming', $event)"
            (complete)="complete($event)"
            (scheduleToday)="scheduleForToday($event)"
            (scheduleDate)="openSchedule($event)"
          />
        </div>
      </div>
    </ng-template>
  `,
})
export class TasksListComponent implements OnInit {
  private readonly tasksService = inject(TasksService);
  private readonly fb = inject(FormBuilder);

  scopeTabs: { value: TaskScope; label: string }[] = [
    { value: 'owned', label: 'My tasks' },
    { value: 'assigned_to_me', label: 'Assigned to me' },
  ];
  viewTabs: { id: TaskTab; label: string }[] = [
    { id: 'today', label: 'Today' },
    { id: 'all', label: 'All tasks' },
  ];

  scope: TaskScope = 'owned';
  activeTab: TaskTab = 'today';
  readonly pageSize = 12;

  stats = { completedToday: 0, streakDays: 0 };
  quickTitle = '';
  quickAdding = false;
  scheduleTaskId: string | null = null;
  scheduleDate = '';
  scheduleTime = '';

  readonly otherViews: ListViewConfig[] = [
    {
      key: 'overdue',
      title: 'Overdue',
      hint: '',
      emptyMessage: '',
      variant: 'overdue',
      query: { overdue: true },
    },
    {
      key: 'nodate',
      title: 'No date',
      hint: '',
      emptyMessage: '',
      variant: 'nodate',
      query: { has_due_date: false },
    },
    {
      key: 'upcoming',
      title: 'Upcoming',
      hint: '',
      emptyMessage: '',
      variant: 'upcoming',
      query: { due_later: true },
    },
  ];

  lists: Record<TaskListKey, TaskListState> = {
    today: { items: [], total: 0, page: 1, loading: false },
    overdue: { items: [], total: 0, page: 1, loading: false },
    nodate: { items: [], total: 0, page: 1, loading: false },
    upcoming: { items: [], total: 0, page: 1, loading: false },
  };

  filters = this.fb.nonNullable.group({
    search: '',
    status: '',
    priority: '',
  });

  get canSchedule(): boolean {
    return this.scope === 'owned';
  }

  get allTasksTotal(): number {
    return this.lists.overdue.total + this.lists.nodate.total + this.lists.upcoming.total;
  }

  ngOnInit(): void {
    this.refresh();
  }

  setScope(scope: TaskScope): void {
    this.scope = scope;
    this.resetPages();
    this.refresh();
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
    this.tasksService.update(id, { due_date: due.toISOString() }).subscribe({ next: () => this.refresh() });
  }

  openSchedule(id: string): void {
    this.scheduleTaskId = id;
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
        this.activeTab = 'all';
        this.refresh();
      },
      error: () => {
        this.quickAdding = false;
      },
    });
  }

  private refresh(reloadStats = true): void {
    const jobs: Observable<unknown>[] = [
      this.fetchList('today'),
      ...this.otherViews.map((v) => this.fetchList(v.key)),
    ];
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
    (['today', 'overdue', 'nodate', 'upcoming'] as TaskListKey[]).forEach((key) => {
      this.lists[key].page = 1;
    });
  }

  private loadList(key: TaskListKey): void {
    this.fetchList(key).subscribe();
  }

  private fetchList(key: TaskListKey): Observable<unknown> {
    const state = this.lists[key];
    state.loading = true;
    const raw = this.filters.getRawValue();
    const offset = (state.page - 1) * this.pageSize;
    const viewQuery =
      key === 'today'
        ? { due_today: true, incomplete_only: true }
        : { ...this.otherViews.find((v) => v.key === key)!.query };

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
          },
        }),
      );
  }
}
