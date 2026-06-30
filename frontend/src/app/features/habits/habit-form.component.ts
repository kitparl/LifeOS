import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { HABIT_FREQUENCIES, HabitFrequency } from './models/habit.models';
import { HabitsService } from './services/habits.service';

@Component({
  selector: 'app-habit-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="max-w-lg">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">{{ isEdit ? 'Edit Habit' : 'New Habit' }}</div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div>
            <label class="mb-1 block">Name</label>
            <input class="input-field" formControlName="name" />
          </div>
          <div>
            <label class="mb-1 block">Frequency</label>
            <select class="input-field" formControlName="frequency">
              @for (f of frequencies; track f.value) {
                <option [value]="f.value">{{ f.label }}</option>
              }
            </select>
          </div>
          <div>
            <label class="mb-1 block">Description</label>
            <textarea class="input-field min-h-[80px]" formControlName="description"></textarea>
          </div>
          @if (isEdit) {
            <label class="flex items-center gap-2">
              <input type="checkbox" formControlName="is_active" />
              Active
            </label>
          }
          @if (error) {
            <p class="text-xs text-red-700">{{ error }}</p>
          }
          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">
              {{ saving ? 'Saving…' : 'Save' }}
            </button>
            <a routerLink="/habits" class="input-field !w-auto inline-flex items-center no-underline text-gray-700">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  `,
})
export class HabitFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly habitsService = inject(HabitsService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  frequencies = HABIT_FREQUENCIES;
  isEdit = false;
  habitId: string | null = null;
  saving = false;
  error = '';

  form = this.fb.nonNullable.group({
    name: ['', Validators.required],
    frequency: ['daily' as HabitFrequency, Validators.required],
    description: [''],
    is_active: [true],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.habitId = id;
      this.habitsService.get(id).subscribe({
        next: (habit) => {
          this.form.patchValue({
            name: habit.name,
            frequency: habit.frequency,
            description: habit.description ?? '',
            is_active: habit.is_active,
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
    const payload = {
      name: raw.name,
      frequency: raw.frequency,
      description: raw.description || null,
      ...(this.isEdit ? { is_active: raw.is_active } : {}),
    };

    const req =
      this.isEdit && this.habitId
        ? this.habitsService.update(this.habitId, payload)
        : this.habitsService.create(payload);

    req.subscribe({
      next: (habit) => this.router.navigate(['/habits', habit.id]),
      error: (err) => {
        this.error = err?.error?.detail || 'Failed to save habit';
        this.saving = false;
      },
    });
  }
}
