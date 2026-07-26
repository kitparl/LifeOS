import { DatePipe } from '@angular/common';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Subscription, distinctUntilChanged, map } from 'rxjs';
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

type DetailTab = 'overview' | 'people' | 'activity';

@Component({
  selector: 'app-task-detail',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe, UserPickerComponent, AttachmentListComponent],
  template: `
    @if (task; as t) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div class="min-w-0">
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
            <div class="mt-1.5 flex flex-wrap gap-1">
              <span class="chip text-xs capitalize">{{ t.priority }}</span>
              <span class="chip text-xs capitalize">{{ t.status.replace('_', ' ') }}</span>
              @if (t.assignment_status) {
                <span class="chip text-xs capitalize">{{ t.assignment_status }}</span>
              }
              @if (t.category) {
                <span class="chip text-xs">{{ t.category }}</span>
              }
              @if (t.archived_at) {
                <span class="chip text-xs" style="color: var(--text-muted)">Archived</span>
              }
            </div>
          </div>
          <div class="flex flex-wrap gap-2">
            @if (t.status !== 'completed' && t.permissions?.can_change_status) {
              <button type="button" class="btn-primary text-xs" (click)="complete()">Mark done</button>
            }
            @if (t.permissions?.can_edit) {
              <a [routerLink]="['/tasks', t.id, 'edit']" class="btn-primary text-xs no-underline">Edit</a>
            }
            @if (t.permissions?.can_archive) {
              @if (!t.archived_at) {
                <button type="button" class="btn-ghost text-xs" (click)="archive()">Archive</button>
              } @else {
                <button type="button" class="btn-ghost text-xs" (click)="restore()">Restore</button>
              }
            }
            @if (t.permissions?.can_delete) {
              <button type="button" class="input-field !w-auto text-xs text-red-700" (click)="remove()">Delete</button>
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

        <div class="flex flex-wrap gap-1.5 text-xs">
          @for (tab of tabs; track tab.value) {
            <button
              type="button"
              class="rounded-lg border px-3 py-1.5"
              [class.bg-[var(--primary-soft)]]="activeTab === tab.value"
              [style.border-color]="'var(--xp-border)'"
              (click)="activeTab = tab.value"
            >
              {{ tab.label }}
            </button>
          }
        </div>

        @if (activeTab === 'overview') {
          <div class="grid gap-3 md:grid-cols-2">
            <div class="panel !p-0 overflow-hidden">
              <div class="title-bar rounded-none border-x-0 border-t-0">Details</div>
              <div class="space-y-2 p-3 text-sm">
                <p>
                  <span class="font-medium">Due:</span>
                  {{ t.due_date ? (t.due_date | date: 'medium') : '—' }}
                </p>
                @if (t.recurrence !== 'none') {
                  <p><span class="font-medium">Repeats:</span> {{ t.recurrence }}</p>
                }
                @if (t.tags.length) {
                  <div class="flex flex-wrap items-center gap-1">
                    <span class="font-medium">Tags:</span>
                    @for (tag of t.tags; track tag) {
                      <span class="chip text-xs">{{ tag }}</span>
                    }
                  </div>
                }
                <div class="space-y-1.5 border-t border-[var(--xp-border)] pt-2">
                  <p>
                    <span class="font-medium">Assignee:</span>
                    @if (t.assignee_username) {
                      <span class="chip text-xs">{{ '@' + t.assignee_username }}</span>
                      <span class="chip text-xs capitalize">{{ t.assignment_status || 'none' }}</span>
                    } @else {
                      <span style="color: var(--text-muted)">Unassigned</span>
                    }
                  </p>
                  @if (t.permissions?.can_assign) {
                    <label class="block text-xs font-medium">Assign user</label>
                    <div class="flex flex-col gap-2 sm:flex-row sm:items-start">
                      <div class="min-w-0 flex-1">
                        <app-user-picker [placeholder]="'Search user to assign…'" (picked)="onAssignee($event)" />
                      </div>
                      <button
                        type="button"
                        class="btn-primary text-xs"
                        [disabled]="!assigneeUsername"
                        (click)="assign()"
                      >
                        Assign
                      </button>
                    </div>
                    @if (t.assignment_id && t.assignee_username) {
                      <button type="button" class="btn-ghost text-xs" (click)="cancelAssignment()">
                        Remove assignment
                      </button>
                    }
                  }
                </div>
                @if (t.permissions?.can_change_status) {
                  <div class="flex flex-wrap items-center gap-2 pt-1">
                    <label class="text-xs font-medium">Status</label>
                    <select class="input-field !w-auto text-xs" [formControl]="statusControl" (change)="changeStatus()">
                      @for (s of statuses; track s.value) {
                        <option [value]="s.value">{{ s.label }}</option>
                      }
                    </select>
                  </div>
                }
              </div>
            </div>

            <div class="panel !p-0 overflow-hidden">
              <div class="title-bar rounded-none border-x-0 border-t-0">Description</div>
              <div class="p-3 text-sm">
                @if (t.description) {
                  <p class="whitespace-pre-wrap" style="color: var(--text-muted)">{{ t.description }}</p>
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
        }

        @if (activeTab === 'people') {
          <div class="grid gap-3 md:grid-cols-2">
            <div class="panel !p-0 overflow-hidden">
              <div class="title-bar rounded-none border-x-0 border-t-0">Assignee</div>
              <div class="space-y-2 p-3 text-sm">
                <p>
                  User:
                  @if (t.assignee_username) {
                    <span class="chip text-xs">{{ '@' + t.assignee_username }}</span>
                  } @else {
                    <span style="color: var(--text-muted)">—</span>
                  }
                </p>
                <p>
                  Status:
                  <span class="chip text-xs capitalize">{{ t.assignment_status || 'none' }}</span>
                </p>
                @if (t.permissions?.can_assign) {
                  <label class="block text-xs font-medium">Assign / reassign</label>
                  <div class="flex flex-col gap-2 sm:flex-row sm:items-start">
                    <div class="min-w-0 flex-1">
                      <app-user-picker (picked)="onAssignee($event)" />
                    </div>
                    <button
                      type="button"
                      class="btn-primary text-xs sm:mt-0"
                      [disabled]="!assigneeUsername"
                      (click)="assign()"
                    >
                      Assign
                    </button>
                  </div>
                  @if (t.assignment_id && t.assignee_username) {
                    <button type="button" class="btn-ghost text-xs" (click)="cancelAssignment()">
                      Remove assignment
                    </button>
                  }
                } @else {
                  <p style="color: var(--text-muted)">Only the owner can reassign this task.</p>
                }
              </div>
            </div>

            <div class="panel !p-0 overflow-hidden">
              <div class="title-bar rounded-none border-x-0 border-t-0">Watchers</div>
              <div class="space-y-2 p-3 text-sm">
                @if (t.permissions?.can_manage_watchers) {
                  <div class="flex flex-col gap-2 sm:flex-row sm:items-start">
                    <div class="min-w-0 flex-1">
                      <app-user-picker (picked)="onWatcher($event)" />
                    </div>
                    <button
                      type="button"
                      class="btn-primary text-xs"
                      [disabled]="!watcherUsername"
                      (click)="addWatcher()"
                    >
                      Add
                    </button>
                  </div>
                }
                @if (watchers.length === 0) {
                  <p style="color: var(--text-muted)">No watchers.</p>
                } @else {
                  <ul class="divide-y divide-[var(--xp-border)]">
                    @for (w of watchers; track w.id) {
                      <li class="flex items-center justify-between gap-2 py-2 text-sm">
                        <span>
                          <span class="font-medium">{{ '@' + (w.username || '') }}</span>
                          <span style="color: var(--text-muted)"> · {{ w.display_name }}</span>
                        </span>
                        @if (t.permissions?.can_manage_watchers) {
                          <button
                            type="button"
                            class="text-xs"
                            style="color: var(--danger)"
                            (click)="removeWatcher(w.user_id)"
                          >
                            Remove
                          </button>
                        }
                      </li>
                    }
                  </ul>
                }
              </div>
            </div>
          </div>
        }

        @if (activeTab === 'activity') {
          <div class="panel !p-0 overflow-hidden">
            <div class="title-bar rounded-none border-x-0 border-t-0">Activity</div>
            <div class="p-3">
              @if (activity.length === 0) {
                <p class="text-sm" style="color: var(--text-muted)">No activity yet.</p>
              } @else {
                <ul class="divide-y divide-[var(--xp-border)] text-sm">
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
                      <span class="shrink-0 text-xs" style="color: var(--text-muted)">{{
                        a.created_at | date: 'short'
                      }}</span>
                    </li>
                  }
                </ul>
              }
            </div>
          </div>

          @if (history.length) {
            <div class="panel !p-0 overflow-hidden">
              <div class="title-bar rounded-none border-x-0 border-t-0">Status history</div>
              <ul class="divide-y divide-[var(--xp-border)] p-0 text-sm">
                @for (h of history; track h.id) {
                  <li class="flex flex-wrap items-baseline justify-between gap-2 px-3 py-2">
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
            </div>
          }
        }

        <a routerLink="/tasks" class="text-sm text-[var(--xp-blue)] underline">Back to tasks</a>
      </div>
    } @else if (loading) {
      <p class="text-sm">Loading task…</p>
    } @else {
      <p class="text-sm text-red-700">Task not found.</p>
    }
  `,
})
export class TaskDetailComponent implements OnInit, OnDestroy {
  private readonly tasksService = inject(TasksService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private routeSub?: Subscription;

  statuses = TASK_STATUSES;
  tabs: { value: DetailTab; label: string }[] = [
    { value: 'overview', label: 'Overview' },
    { value: 'people', label: 'People' },
    { value: 'activity', label: 'Activity' },
  ];
  activeTab: DetailTab = 'overview';
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
    this.routeSub = this.route.paramMap
      .pipe(
        map((params) => params.get('id')),
        distinctUntilChanged(),
      )
      .subscribe((id) => {
        if (id) {
          this.activeTab = 'overview';
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

  ngOnDestroy(): void {
    this.routeSub?.unsubscribe();
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
    this.tasksService.archive(this.task.id).subscribe({ next: () => this.load(this.task!.id) });
  }

  restore(): void {
    if (!this.task) return;
    this.tasksService.restore(this.task.id).subscribe({ next: () => this.load(this.task!.id) });
  }

  remove(): void {
    if (!this.task || !confirm('Delete this task?')) return;
    this.tasksService.delete(this.task.id).subscribe({ next: () => this.router.navigate(['/tasks']) });
  }
}
