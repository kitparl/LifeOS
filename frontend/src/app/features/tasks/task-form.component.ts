import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { TASK_PRIORITIES, TASK_RECURRENCE, TaskPriority, TaskRecurrence } from './models/task.models';
import { TasksService } from './services/tasks.service';

@Component({
  selector: 'app-task-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="max-w-lg">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">{{ isEdit ? 'Edit Task' : 'New Task' }}</div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div>
            <label class="mb-1 block">Title</label>
            <input class="input-field" formControlName="title" />
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="mb-1 block">Priority</label>
              <select class="input-field" formControlName="priority">
                @for (p of priorities; track p.value) {
                  <option [value]="p.value">{{ p.label }}</option>
                }
              </select>
            </div>
            <div>
              <label class="mb-1 block">Recurrence</label>
              <select class="input-field" formControlName="recurrence">
                @for (r of recurrences; track r.value) {
                  <option [value]="r.value">{{ r.label }}</option>
                }
              </select>
            </div>
          </div>
          <div>
            <label class="mb-1 block">Category</label>
            <input class="input-field" formControlName="category" placeholder="e.g. work, personal" />
          </div>
          <div>
            <label class="mb-1 block">Tags (comma-separated)</label>
            <input class="input-field" formControlName="tags" />
          </div>
          <div>
            <label class="mb-1 block">Description</label>
            <textarea class="input-field min-h-[80px]" formControlName="description"></textarea>
          </div>
          <div>
            <label class="mb-1 block">Due date</label>
            <input class="input-field" type="datetime-local" formControlName="due_date" />
          </div>
          @if (error) {
            <p class="text-xs text-red-700">{{ error }}</p>
          }
          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">
              {{ saving ? 'Saving…' : 'Save' }}
            </button>
            <a routerLink="/tasks" class="input-field !w-auto inline-flex items-center no-underline text-gray-700">Cancel</a>
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
  recurrences = TASK_RECURRENCE;
  isEdit = false;
  taskId: string | null = null;
  saving = false;
  error = '';

  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    priority: ['medium' as TaskPriority, Validators.required],
    recurrence: ['none' as TaskRecurrence, Validators.required],
    category: [''],
    tags: [''],
    description: [''],
    due_date: [''],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.taskId = id;
      this.tasksService.get(id).subscribe({
        next: (task) => {
          this.form.patchValue({
            title: task.title,
            priority: task.priority,
            recurrence: task.recurrence,
            category: task.category ?? '',
            tags: task.tags.join(', '),
            description: task.description ?? '',
            due_date: task.due_date ? task.due_date.slice(0, 16) : '',
          });
        },
      });
    }
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
    const payload = {
      title: raw.title,
      priority: raw.priority,
      recurrence: raw.recurrence,
      category: raw.category || null,
      tags,
      description: raw.description || null,
      due_date: raw.due_date ? new Date(raw.due_date).toISOString() : null,
    };

    const req =
      this.isEdit && this.taskId
        ? this.tasksService.update(this.taskId, payload)
        : this.tasksService.create(payload);

    req.subscribe({
      next: (task) => this.router.navigate(['/tasks', task.id]),
      error: (err) => {
        this.error = err?.error?.detail || 'Failed to save task';
        this.saving = false;
      },
    });
  }
}
