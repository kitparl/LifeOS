import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Task } from './models/task.models';
import { TasksService } from './services/tasks.service';

@Component({
  selector: 'app-task-detail',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe],
  template: `
    @if (task; as t) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 class="text-lg font-semibold" [class.line-through]="t.status === 'completed'">{{ t.title }}</h1>
            <p class="text-xs capitalize text-gray-600">
              {{ t.priority }} priority · {{ t.status.replace('_', ' ') }}
              @if (t.category) { · {{ t.category }} }
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            @if (t.status !== 'completed') {
              <button type="button" class="btn-primary text-xs" (click)="complete()">Mark done</button>
            }
            <a [routerLink]="['/tasks', t.id, 'edit']" class="btn-primary text-xs no-underline">Edit</a>
            <button type="button" class="input-field !w-auto text-xs text-red-700" (click)="remove()">Delete</button>
          </div>
        </div>

        <div class="grid gap-3 md:grid-cols-2">
          <div class="panel text-sm space-y-1">
            @if (t.due_date) {
              <p><span class="font-medium">Due:</span> {{ t.due_date | date: 'medium' }}</p>
            }
            @if (t.recurrence !== 'none') {
              <p><span class="font-medium">Repeats:</span> {{ t.recurrence }}</p>
            }
            @if (t.tags.length) {
              <p><span class="font-medium">Tags:</span> {{ t.tags.join(', ') }}</p>
            }
          </div>
          @if (t.description) {
            <div class="panel text-sm">
              <p class="font-medium mb-1">Description</p>
              <p class="whitespace-pre-wrap text-gray-700">{{ t.description }}</p>
            </div>
          }
        </div>

        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Subtasks</div>
          <div class="p-3 space-y-2">
            <form class="flex gap-2" [formGroup]="subtaskForm" (ngSubmit)="addSubtask()">
              <input class="input-field flex-1" formControlName="title" placeholder="New subtask…" />
              <button type="submit" class="btn-primary text-xs" [disabled]="subtaskForm.invalid">Add</button>
            </form>
            @if (t.subtasks.length === 0) {
              <p class="text-sm text-gray-600">No subtasks yet.</p>
            } @else {
              <ul class="divide-y divide-[var(--xp-border)] text-sm">
                @for (s of t.subtasks; track s.id) {
                  <li class="flex items-center justify-between gap-2 py-2">
                    <span [class.line-through]="s.status === 'completed'">{{ s.title }}</span>
                    <div class="flex gap-2">
                      @if (s.status !== 'completed') {
                        <button type="button" class="text-xs text-green-700" (click)="completeSubtask(s.id)">Done</button>
                      }
                    </div>
                  </li>
                }
              </ul>
            }
          </div>
        </div>

        <a routerLink="/tasks" class="text-sm text-[var(--xp-blue)] underline">Back to tasks</a>
      </div>
    } @else if (loading) {
      <p class="text-sm">Loading task…</p>
    } @else {
      <p class="text-sm text-red-700">Task not found.</p>
    }
  `,
})
export class TaskDetailComponent implements OnInit {
  private readonly tasksService = inject(TasksService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);

  task: Task | null = null;
  loading = false;
  subtaskForm = this.fb.nonNullable.group({ title: [''] });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) this.load(id);
  }

  load(id: string): void {
    this.loading = true;
    this.tasksService.get(id).subscribe({
      next: (t) => {
        this.task = t;
        this.loading = false;
      },
      error: () => {
        this.task = null;
        this.loading = false;
      },
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

  remove(): void {
    if (!this.task || !confirm('Delete this task?')) return;
    this.tasksService.delete(this.task.id).subscribe({ next: () => this.router.navigate(['/tasks']) });
  }
}
