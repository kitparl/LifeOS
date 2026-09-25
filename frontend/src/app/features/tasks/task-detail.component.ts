import { DatePipe } from '@angular/common';
import { Component, DestroyRef, HostListener, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { distinctUntilChanged, map } from 'rxjs';
import { PublicUser } from '../../core/models/auth.models';
import { UserPickerComponent } from './components/user-picker.component';
import { AttachmentListComponent } from '../files/components/attachment-list.component';
import {
  ActivityLogEntry,
  StatusHistoryEntry,
  TASK_STATUSES,
  Task,
  TaskNote,
  TaskStatus,
  TaskWatcher,
} from './models/task.models';
import { TasksService } from './services/tasks.service';

@Component({
  selector: 'app-task-detail',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe, UserPickerComponent, AttachmentListComponent],
  template: `
    @if (task; as t) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div class="min-w-0 flex-1">
            @if (t.parent_id) {
              <a [routerLink]="['/tasks', t.parent_id]" class="mb-1 block text-xs text-[var(--xp-blue)] underline">
                ← Back to parent task
              </a>
            }
            <h1
              class="text-lg font-semibold"
              [class.line-through]="t.status === 'completed'"
              [class.text-[var(--text-muted)]]="t.status === 'completed'"
            >
              {{ t.title }}
            </h1>
            <div class="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs" style="color: var(--text-muted)">
              @if (t.permissions?.can_change_status) {
                <label for="task-status-select" class="sr-only">Status</label>
                <select
                  id="task-status-select"
                  class="input-field !w-auto !py-0.5 text-xs"
                  [formControl]="statusControl"
                  (change)="changeStatus()"
                >
                  @for (s of statuses; track s.value) {
                    <option [value]="s.value">{{ s.label }}</option>
                  }
                </select>
              } @else {
                <span class="capitalize">{{ t.status.replace('_', ' ') }}</span>
              }
              <span class="capitalize">· {{ t.priority }} priority</span>
              @if (t.category) {
                <span>· {{ t.category }}</span>
              }
              @if (t.archived_at) {
                <span class="chip text-xs">Archived</span>
              }
            </div>
          </div>
          <div class="flex items-center gap-2">
            @if (t.status !== 'completed' && t.permissions?.can_change_status) {
              <button type="button" class="btn-primary text-xs" (click)="complete()">Mark done</button>
            }
            @if (t.permissions?.can_edit) {
              <a [routerLink]="['/tasks', t.id, 'edit']" class="btn-secondary text-xs no-underline">Edit</a>
            }
            @if (t.permissions?.can_archive || t.permissions?.can_delete) {
              <div class="relative" (click)="$event.stopPropagation()" (keydown.escape)="moreOpen = false">
                <button
                  type="button"
                  class="btn-ghost text-xs"
                  aria-haspopup="menu"
                  [attr.aria-expanded]="moreOpen"
                  (click)="moreOpen = !moreOpen"
                >
                  More
                </button>
                @if (moreOpen) {
                  <div class="menu absolute right-0 z-30 mt-1 p-1" role="menu">
                    @if (t.permissions?.can_archive) {
                      @if (!t.archived_at) {
                        <button type="button" class="menu-item" role="menuitem" (click)="archive()">Archive</button>
                      } @else {
                        <button type="button" class="menu-item" role="menuitem" (click)="restore()">Restore</button>
                      }
                    }
                    @if (t.permissions?.can_delete) {
                      <button type="button" class="menu-item menu-item--danger" role="menuitem" (click)="remove()">
                        Delete
                      </button>
                    }
                  </div>
                }
              </div>
            }
          </div>
        </div>

        @if (t.assignment_status === 'pending' && t.permissions?.role === 'assignee' && t.assignment_id) {
          <div class="panel !p-0 overflow-hidden" style="border-color: color-mix(in srgb, var(--xp-blue) 40%, var(--xp-border))">
            <div class="title-bar rounded-none border-x-0 border-t-0">Assignment pending</div>
            <div class="flex flex-wrap items-center justify-between gap-2 p-3 text-sm">
              <p style="color: var(--text-muted)">Accept this task to start working on it.</p>
              <div class="flex gap-2">
                <button type="button" class="btn-primary text-xs" (click)="accept()">Accept</button>
                <button type="button" class="btn-ghost text-xs" (click)="reject()">Reject</button>
              </div>
            </div>
          </div>
        }

        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Details</div>
          <div class="space-y-3 p-3 text-sm">
            <dl class="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5">
              <dt class="font-medium">Due</dt>
              <dd>{{ t.due_date ? (t.due_date | date: 'medium') : 'No date' }}</dd>
              @if (t.recurrence !== 'none') {
                <dt class="font-medium">Repeats</dt>
                <dd class="capitalize">{{ t.recurrence }}</dd>
              }
              @if (t.tags.length) {
                <dt class="font-medium">Tags</dt>
                <dd class="flex flex-wrap gap-1">
                  @for (tag of t.tags; track tag) {
                    <span class="chip text-xs">{{ tag }}</span>
                  }
                </dd>
              }
              @if (t.assignee_username) {
                <dt class="font-medium">Assignee</dt>
                <dd>
                  {{ '@' + t.assignee_username }}
                  @if (t.assignment_status) {
                    <span class="capitalize" style="color: var(--text-muted)">· {{ t.assignment_status }}</span>
                  }
                </dd>
              }
            </dl>
            <div class="border-t border-[var(--xp-border)] pt-3">
              @if (t.description) {
                <p class="whitespace-pre-wrap">{{ t.description }}</p>
              } @else {
                <p style="color: var(--text-muted)">No description</p>
              }
            </div>
          </div>
        </div>

        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Subtasks</div>
          <div class="space-y-2 p-3">
            <form class="flex flex-col gap-2 sm:flex-row" [formGroup]="subtaskForm" (ngSubmit)="addSubtask()">
              <input class="input-field flex-1" formControlName="title" placeholder="New subtask…" />
              <button type="submit" class="btn-primary text-xs sm:w-auto" [disabled]="subtaskForm.invalid">Add</button>
            </form>
            @if (t.subtasks.length === 0) {
              <p class="text-sm" style="color: var(--text-muted)">No subtasks yet. Add one to break work down.</p>
            } @else {
              <ul class="divide-y divide-[var(--xp-border)] text-sm">
                @for (s of t.subtasks; track s.id) {
                  <li class="space-y-2 py-2">
                    <div class="flex flex-wrap items-center justify-between gap-2">
                      <div class="min-w-0 flex-1">
                        <a
                          [routerLink]="['/tasks', s.id]"
                          class="link font-medium"
                          [class.line-through]="s.status === 'completed'"
                        >
                          {{ s.title }}
                        </a>
                        @if (s.assignee_username) {
                          <span class="ml-2 chip text-xs">{{ '@' + s.assignee_username }}</span>
                          @if (s.assignment_status) {
                            <span class="chip text-xs capitalize">{{ s.assignment_status }}</span>
                          }
                        }
                      </div>
                      <div class="flex flex-wrap gap-1">
                        @if (t.permissions?.can_assign && s.status !== 'completed') {
                          <button
                            type="button"
                            class="btn-ghost text-xs"
                            (click)="toggleSubtaskAssign(s.id)"
                          >
                            {{ assigningSubtaskId === s.id ? 'Cancel' : 'Assign' }}
                          </button>
                        }
                        @if (s.status !== 'completed') {
                          <button type="button" class="btn-ghost text-xs" (click)="completeSubtask(s.id)">Done</button>
                        } @else {
                          <span class="chip text-xs">Done</span>
                        }
                      </div>
                    </div>
                    @if (assigningSubtaskId === s.id) {
                      <div class="flex flex-col gap-2 rounded border border-[var(--xp-border)] p-2 sm:flex-row sm:items-start">
                        <div class="min-w-0 flex-1">
                          <app-user-picker
                            [placeholder]="'Assign subtask to…'"
                            (picked)="onSubtaskAssignee($event)"
                          />
                        </div>
                        <button
                          type="button"
                          class="btn-primary text-xs"
                          [disabled]="!subtaskAssigneeUsername"
                          (click)="assignSubtask(s.id, s.assignee_username)"
                        >
                          Assign user
                        </button>
                      </div>
                    }
                  </li>
                }
              </ul>
            }
          </div>
        </div>

        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Notes</div>
          <div class="space-y-2 p-3">
            @if (t.permissions?.can_add_note) {
              <form class="flex flex-col gap-2 sm:flex-row" [formGroup]="noteForm" (ngSubmit)="addNote()">
                <input class="input-field flex-1" formControlName="body" placeholder="Add a note…" />
                <button type="submit" class="btn-primary text-xs sm:w-auto">Add</button>
              </form>
            }
            @if (notes.length === 0) {
              <p class="text-sm" style="color: var(--text-muted)">No notes yet.</p>
            } @else {
              <ul class="divide-y divide-[var(--xp-border)] text-sm">
                @for (n of notes; track n.id) {
                  <li class="py-2">
                    <p class="whitespace-pre-wrap">{{ n.body }}</p>
                    <p class="mt-1 text-xs" style="color: var(--text-muted)">{{ n.created_at | date: 'short' }}</p>
                  </li>
                }
              </ul>
            }
          </div>
        </div>

        <app-attachment-list module="tasks" [entityId]="t.id" />

        <details class="panel !p-0 overflow-hidden">
          <summary class="flex cursor-pointer items-center justify-between gap-2 px-3 py-2 text-sm">
            <span class="font-medium">People</span>
            <span class="text-xs" style="color: var(--text-muted)">
              {{ t.assignee_username ? '@' + t.assignee_username : 'Unassigned' }} · {{ watchers.length }}
              {{ watchers.length === 1 ? 'watcher' : 'watchers' }}
            </span>
          </summary>
          <div class="grid gap-4 border-t border-[var(--xp-border)] p-3 text-sm md:grid-cols-2">
            <section class="space-y-2">
              <h2 class="text-xs font-semibold uppercase tracking-wide" style="color: var(--text-muted)">Assignee</h2>
              <p>
                @if (t.assignee_username) {
                  <span class="chip text-xs">{{ '@' + t.assignee_username }}</span>
                  <span class="capitalize" style="color: var(--text-muted)"> · {{ t.assignment_status || 'none' }}</span>
                } @else {
                  <span style="color: var(--text-muted)">Unassigned</span>
                }
              </p>
              @if (t.permissions?.can_assign) {
                <label class="block text-xs font-medium">Assign / reassign</label>
                <div class="flex flex-col gap-2 sm:flex-row sm:items-start">
                  <div class="min-w-0 flex-1">
                    <app-user-picker [placeholder]="'Search user to assign…'" (picked)="onAssignee($event)" />
                  </div>
                  <button type="button" class="btn-primary text-xs" [disabled]="!assigneeUsername" (click)="assign()">
                    Assign
                  </button>
                </div>
                @if (t.assignment_id && t.assignee_username) {
                  <button type="button" class="btn-ghost text-xs" (click)="cancelAssignment()">Remove assignment</button>
                }
              } @else {
                <p style="color: var(--text-muted)">Only the owner can reassign this task.</p>
              }
            </section>

            <section class="space-y-2">
              <h2 class="text-xs font-semibold uppercase tracking-wide" style="color: var(--text-muted)">Watchers</h2>
              @if (t.permissions?.can_manage_watchers) {
                <div class="flex flex-col gap-2 sm:flex-row sm:items-start">
                  <div class="min-w-0 flex-1">
                    <app-user-picker (picked)="onWatcher($event)" />
                  </div>
                  <button type="button" class="btn-primary text-xs" [disabled]="!watcherUsername" (click)="addWatcher()">
                    Add
                  </button>
                </div>
              }
              @if (watchers.length === 0) {
                <p style="color: var(--text-muted)">No watchers.</p>
              } @else {
                <ul class="divide-y divide-[var(--xp-border)]">
                  @for (w of watchers; track w.id) {
                    <li class="flex items-center justify-between gap-2 py-2">
                      <span>
                        <span class="font-medium">{{ '@' + (w.username || '') }}</span>
                        <span style="color: var(--text-muted)"> · {{ w.display_name }}</span>
                      </span>
                      @if (t.permissions?.can_manage_watchers) {
                        <button type="button" class="text-xs" style="color: var(--danger)" (click)="removeWatcher(w.user_id)">
                          Remove
                        </button>
                      }
                    </li>
                  }
                </ul>
              }
            </section>
          </div>
        </details>

        <details class="panel !p-0 overflow-hidden">
          <summary class="flex cursor-pointer items-center justify-between gap-2 px-3 py-2 text-sm">
            <span class="font-medium">Activity</span>
            <span class="text-xs" style="color: var(--text-muted)">
              {{ activity.length }} {{ activity.length === 1 ? 'update' : 'updates' }}
            </span>
          </summary>
          <div class="space-y-4 border-t border-[var(--xp-border)] p-3 text-sm">
            @if (activity.length === 0) {
              <p style="color: var(--text-muted)">No activity yet.</p>
            } @else {
              <ul class="divide-y divide-[var(--xp-border)]">
                @for (a of activity; track a.id) {
                  <li class="flex flex-wrap items-baseline justify-between gap-2 py-2">
                    <div>
                      <span class="font-medium capitalize">{{ a.action.replace('_', ' ') }}</span>
                      @if (a.field) {
                        <span style="color: var(--text-muted)"> · {{ a.field }}</span>
                      }
                      @if (a.old_value || a.new_value) {
                        <span style="color: var(--text-muted)">
                          : {{ a.old_value || '—' }} → {{ a.new_value || '—' }}
                        </span>
                      }
                    </div>
                    <span class="shrink-0 text-xs" style="color: var(--text-muted)">{{ a.created_at | date: 'short' }}</span>
                  </li>
                }
              </ul>
            }

            @if (history.length) {
              <section class="space-y-1">
                <h2 class="text-xs font-semibold uppercase tracking-wide" style="color: var(--text-muted)">
                  Status history
                </h2>
                <ul class="divide-y divide-[var(--xp-border)]">
                  @for (h of history; track h.id) {
                    <li class="flex flex-wrap items-baseline justify-between gap-2 py-2">
                      <span>
                        <span class="capitalize">{{ h.from_status || 'new' }}</span>
                        →
                        <span class="font-medium capitalize">{{ h.to_status }}</span>
                        @if (h.reason) {
                          <span style="color: var(--text-muted)"> · {{ h.reason }}</span>
                        }
                      </span>
                      <span class="text-xs" style="color: var(--text-muted)">{{ h.created_at | date: 'short' }}</span>
                    </li>
                  }
                </ul>
              </section>
            }
          </div>
        </details>

        <a routerLink="/tasks" class="text-sm text-[var(--xp-blue)] underline">Back to tasks</a>
      </div>
    } @else if (loading) {
      <p class="text-sm" role="status">Loading task…</p>
    } @else {
      <div class="panel space-y-2 text-sm" role="alert">
        <p style="color: var(--danger)">Task not found or couldn't be loaded.</p>
        <a routerLink="/tasks" class="btn-secondary inline-block text-xs no-underline">Back to tasks</a>
      </div>
    }
  `,
})
export class TaskDetailComponent implements OnInit {
  private readonly tasksService = inject(TasksService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly destroyRef = inject(DestroyRef);

  statuses = TASK_STATUSES;
  moreOpen = false;
  task: Task | null = null;
  loading = false;
  notes: TaskNote[] = [];
  watchers: TaskWatcher[] = [];
  activity: ActivityLogEntry[] = [];
  history: StatusHistoryEntry[] = [];
  assigneeUsername: string | null = null;
  watcherUsername: string | null = null;
  assigningSubtaskId: string | null = null;
  subtaskAssigneeUsername: string | null = null;

  subtaskForm = this.fb.nonNullable.group({ title: [''] });
  noteForm = this.fb.nonNullable.group({ body: [''] });
  statusControl = this.fb.nonNullable.control<TaskStatus>('pending');

  ngOnInit(): void {
    // Re-load when navigating parent ↔ subtask (same component instance).
    this.route.paramMap
      .pipe(
        map((params) => params.get('id')),
        distinctUntilChanged(),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((id) => {
        if (id) {
          this.moreOpen = false;
          this.assigneeUsername = null;
          this.watcherUsername = null;
          this.assigningSubtaskId = null;
          this.subtaskAssigneeUsername = null;
          this.subtaskForm.reset({ title: '' });
          this.noteForm.reset({ body: '' });
          this.load(id);
        }
      });
  }

  @HostListener('document:click')
  closeMoreMenu(): void {
    this.moreOpen = false;
  }

  load(id: string): void {
    this.loading = true;
    this.tasksService.get(id).subscribe({
      next: (t) => {
        this.task = t;
        this.statusControl.setValue(t.status === 'done' ? 'completed' : t.status);
        this.loading = false;
        this.loadExtras(id);
      },
      error: () => {
        this.task = null;
        this.loading = false;
      },
    });
  }

  loadExtras(id: string): void {
    this.tasksService.listNotes(id).subscribe({ next: (n) => (this.notes = n) });
    this.tasksService.listWatchers(id).subscribe({ next: (w) => (this.watchers = w) });
    this.tasksService.activity(id).subscribe({ next: (a) => (this.activity = a) });
    this.tasksService.statusHistory(id).subscribe({ next: (h) => (this.history = h) });
  }

  onAssignee(user: PublicUser | null): void {
    this.assigneeUsername = user?.username ?? null;
  }

  onWatcher(user: PublicUser | null): void {
    this.watcherUsername = user?.username ?? null;
  }

  onSubtaskAssignee(user: PublicUser | null): void {
    this.subtaskAssigneeUsername = user?.username ?? null;
  }

  toggleSubtaskAssign(subtaskId: string): void {
    if (this.assigningSubtaskId === subtaskId) {
      this.assigningSubtaskId = null;
      this.subtaskAssigneeUsername = null;
      return;
    }
    this.assigningSubtaskId = subtaskId;
    this.subtaskAssigneeUsername = null;
  }

  private confirmAssign(username: string, currentUsername: string | null | undefined, label: string): boolean {
    if (currentUsername && currentUsername !== username) {
      return confirm(
        `Reassign this ${label} to @${username}?\n\n@${currentUsername} will be notified that it was assigned to another user.`,
      );
    }
    return confirm(`Assign this ${label} to @${username}?\n\nThey will get a notification.`);
  }

  assign(): void {
    if (!this.task || !this.assigneeUsername) return;
    if (!this.confirmAssign(this.assigneeUsername, this.task.assignee_username, 'task')) return;
    this.tasksService.assign(this.task.id, { assignee_username: this.assigneeUsername }).subscribe({
      next: () => {
        this.assigneeUsername = null;
        this.load(this.task!.id);
      },
    });
  }

  assignSubtask(subtaskId: string, currentUsername: string | null | undefined): void {
    if (!this.task || !this.subtaskAssigneeUsername) return;
    if (!this.confirmAssign(this.subtaskAssigneeUsername, currentUsername, 'subtask')) return;
    this.tasksService.assign(subtaskId, { assignee_username: this.subtaskAssigneeUsername }).subscribe({
      next: () => {
        this.assigningSubtaskId = null;
        this.subtaskAssigneeUsername = null;
        this.load(this.task!.id);
      },
    });
  }

  cancelAssignment(): void {
    if (!this.task?.assignment_id) return;
    const who = this.task.assignee_username ? `@${this.task.assignee_username}` : 'the current assignee';
    if (
      !confirm(
        `Remove assignment from ${who}?\n\nThey will be notified that the assignment was removed.`,
      )
    ) {
      return;
    }
    this.tasksService.cancelAssignment(this.task.id, this.task.assignment_id).subscribe({
      next: () => this.load(this.task!.id),
    });
  }

  accept(): void {
    if (!this.task?.assignment_id) return;
    this.tasksService.acceptAssignment(this.task.id, this.task.assignment_id).subscribe({
      next: () => this.load(this.task!.id),
    });
  }

  reject(): void {
    if (!this.task?.assignment_id) return;
    const reason = prompt('Reason (optional)') || undefined;
    this.tasksService.rejectAssignment(this.task.id, this.task.assignment_id, reason).subscribe({
      next: () => this.load(this.task!.id),
    });
  }

  changeStatus(): void {
    if (!this.task) return;
    this.tasksService.update(this.task.id, { status: this.statusControl.value, version: this.task.version }).subscribe({
      next: () => this.load(this.task!.id),
    });
  }

  addNote(): void {
    if (!this.task) return;
    const body = this.noteForm.getRawValue().body.trim();
    if (!body) return;
    this.tasksService.addNote(this.task.id, body).subscribe({
      next: () => {
        this.noteForm.reset({ body: '' });
        this.loadExtras(this.task!.id);
      },
    });
  }

  addWatcher(): void {
    if (!this.task || !this.watcherUsername) return;
    this.tasksService.addWatcher(this.task.id, { username: this.watcherUsername }).subscribe({
      next: () => this.loadExtras(this.task!.id),
    });
  }

  removeWatcher(userId: string): void {
    if (!this.task) return;
    this.tasksService.removeWatcher(this.task.id, userId).subscribe({
      next: () => this.loadExtras(this.task!.id),
    });
  }

  addSubtask(): void {
    if (!this.task || this.subtaskForm.invalid) return;
    const title = this.subtaskForm.getRawValue().title.trim();
    if (!title) return;
    this.tasksService.create({ title, parent_id: this.task.id }).subscribe({
      next: () => {
        this.subtaskForm.reset({ title: '' });
        this.load(this.task!.id);
      },
    });
  }

  completeSubtask(id: string): void {
    if (!this.task) return;
    this.tasksService.complete(id).subscribe({ next: () => this.load(this.task!.id) });
  }

  complete(): void {
    if (!this.task) return;
    this.tasksService.complete(this.task.id).subscribe({ next: () => this.load(this.task!.id) });
  }

  archive(): void {
    if (!this.task) return;
    this.moreOpen = false;
    this.tasksService.archive(this.task.id).subscribe({ next: () => this.load(this.task!.id) });
  }

  restore(): void {
    if (!this.task) return;
    this.moreOpen = false;
    this.tasksService.restore(this.task.id).subscribe({ next: () => this.load(this.task!.id) });
  }

  remove(): void {
    this.moreOpen = false;
    if (!this.task || !confirm('Delete this task?')) return;
    this.tasksService.delete(this.task.id).subscribe({ next: () => this.router.navigate(['/tasks']) });
  }
}
