import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { PublicUser } from '../../core/models/auth.models';
import { UserPickerComponent } from './components/user-picker.component';
import { TASK_PRIORITIES, TASK_RECURRENCE, TASK_STATUSES, TaskPriority, TaskRecurrence, TaskStatus } from './models/task.models';
import { combineDueDate, splitDueDate } from './task-due-date.util';
import { TasksService } from './services/tasks.service';
import { localIsoDate } from '../../core/utils/date';
import { apiErrorMessage } from '../../core/utils/http';

@Component({
  selector: 'app-task-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, UserPickerComponent],
  template: `
    <div class="max-w-lg">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">{{ isEdit ? 'Edit Task' : 'New Task' }}</div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div>
            <label for="task-title" class="mb-1 block">Title</label>
            <input id="task-title" class="input-field" formControlName="title" maxlength="200" autofocus />
          </div>
          <div>
            <label for="task-due-date" class="mb-1 block">Due date</label>
            <div class="flex flex-wrap items-center gap-2">
              <input id="task-due-date" class="input-field min-w-[10rem] flex-1" type="date" formControlName="due_date" />
              <input class="input-field !w-auto" type="time" formControlName="due_time" aria-label="Due time (optional)" />
              <button type="button" class="btn-ghost text-xs shrink-0" (click)="clearDueDate()">Clear</button>
            </div>
            <p class="mt-1 text-xs" style="color: var(--text-muted)">Time is optional. Clear for no date.</p>
          </div>
          <div>
            <label for="task-priority" class="mb-1 block">Priority</label>
            <select id="task-priority" class="input-field" formControlName="priority">
              @for (p of priorities; track p.value) {
                <option [value]="p.value">{{ p.label }}</option>
              }
            </select>
          </div>

          <details class="rounded border border-[var(--xp-border)]" [open]="showMore">
            <summary class="flex cursor-pointer list-none items-center justify-between gap-2 px-3 py-2">
              <span class="font-medium">More options</span>
              <span class="hidden truncate text-xs sm:inline" style="color: var(--text-muted)">{{ moreSummary }}</span>
            </summary>
            <div class="space-y-3 border-t border-[var(--xp-border)] p-3">
              <div>
                <label for="task-description" class="mb-1 block">Description</label>
                <textarea id="task-description" class="input-field min-h-[80px]" formControlName="description"></textarea>
              </div>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label for="task-status" class="mb-1 block">Status</label>
                  <select id="task-status" class="input-field" formControlName="status">
                    @for (s of statuses; track s.value) {
                      <option [value]="s.value">{{ s.label }}</option>
                    }
                  </select>
                </div>
                <div>
                  <label for="task-recurrence" class="mb-1 block">Repeat</label>
                  <select id="task-recurrence" class="input-field" formControlName="recurrence">
                    @for (r of recurrences; track r.value) {
                      <option [value]="r.value">{{ r.label }}</option>
                    }
                  </select>
                </div>
              </div>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label for="task-category" class="mb-1 block">Category</label>
                  <input id="task-category" class="input-field" formControlName="category" placeholder="e.g. work, personal" />
                </div>
                <div>
                  <label for="task-tags" class="mb-1 block">Tags (comma-separated)</label>
                  <input id="task-tags" class="input-field" formControlName="tags" />
                </div>
              </div>
              @if (!isEdit) {
                <div>
                  <label class="mb-1 block">Assign to (optional — defaults to you)</label>
                  <app-user-picker (picked)="onAssignee($event)" />
                </div>
              }
            </div>
          </details>

          @if (error) {
            <p class="text-xs" style="color: var(--danger)" role="alert">{{ error }}</p>
          }
          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">
              {{ saving ? 'Saving…' : isEdit ? 'Save' : 'Create task' }}
            </button>
            <a [routerLink]="isEdit && taskId ? ['/tasks', taskId] : ['/tasks']" class="btn-secondary no-underline">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  `,
})
export class TaskFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly tasksService = inject(TasksService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  priorities = TASK_PRIORITIES;
  statuses = TASK_STATUSES;
  recurrences = TASK_RECURRENCE;
  isEdit = false;
  taskId: string | null = null;
  saving = false;
  error = '';
  assigneeUsername: string | null = null;
  /** Expanded when editing a task that already uses advanced fields. */
  showMore = false;

  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    priority: ['medium' as TaskPriority, Validators.required],
    status: ['pending' as TaskStatus, Validators.required],
    recurrence: ['none' as TaskRecurrence, Validators.required],
    category: [''],
    tags: [''],
    description: [''],
    due_date: [localIsoDate()],
    due_time: [''],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.taskId = id;
      this.tasksService.get(id).subscribe({
        next: (task) => {
          const due = splitDueDate(task.due_date);
          this.form.patchValue({
            title: task.title,
            priority: task.priority,
            status: task.status === 'done' ? 'completed' : task.status,
            recurrence: task.recurrence,
            category: task.category ?? '',
            tags: task.tags.join(', '),
            description: task.description ?? '',
            due_date: due.date,
            due_time: due.time,
          });
          const raw = this.form.getRawValue();
          this.showMore =
            raw.status !== 'pending' || raw.recurrence !== 'none' || !!raw.category || !!raw.tags || !!raw.description;
        },
      });
    }
  }

  get moreSummary(): string {
    return this.isEdit
      ? 'Description, status, repeat, category, tags'
      : 'Description, status, repeat, category, tags, assignee';
  }

  clearDueDate(): void {
    this.form.patchValue({ due_date: '', due_time: '' });
  }

  onAssignee(user: PublicUser | null): void {
    this.assigneeUsername = user?.username ?? null;
  }

  submit(): void {
    if (this.form.invalid) return;
    this.saving = true;
    this.error = '';
    const raw = this.form.getRawValue();
    const tags = raw.tags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);
    const payload: Record<string, unknown> = {
      title: raw.title,
      priority: raw.priority,
      status: raw.status,
      recurrence: raw.recurrence,
      category: raw.category || null,
      tags,
      description: raw.description || null,
      due_date: combineDueDate(raw.due_date, raw.due_time),
    };
    if (!this.isEdit && this.assigneeUsername) {
      payload['assignee_username'] = this.assigneeUsername;
    }

    const req =
      this.isEdit && this.taskId
        ? this.tasksService.update(this.taskId, payload as never)
        : this.tasksService.create(payload as never);

    req.subscribe({
      next: (task) => this.router.navigate(['/tasks', task.id]),
      error: (err) => {
        this.error = apiErrorMessage(err, 'Failed to save task');
        this.saving = false;
      },
    });
  }
}
