import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { GOAL_CATEGORIES, GOAL_PERIODS, GoalCategory, GoalPeriod } from './models/goal.models';
import { GoalsService } from './services/goals.service';

@Component({
  selector: 'app-goal-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="max-w-lg">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">{{ isEdit ? 'Edit Goal' : 'New Goal' }}</div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div>
            <label class="mb-1 block">Title</label>
            <input class="input-field" formControlName="title" />
          </div>
          <div class="grid gap-3 sm:grid-cols-2">
            <div>
              <label class="mb-1 block">Category</label>
              <select class="input-field" formControlName="category">
                @for (c of categories; track c.value) {
                  <option [value]="c.value">{{ c.label }}</option>
                }
              </select>
            </div>
            <div>
              <label class="mb-1 block">Period</label>
              <select class="input-field" formControlName="period">
                @for (p of periods; track p.value) {
                  <option [value]="p.value">{{ p.label }}</option>
                }
              </select>
            </div>
          </div>
          @if (form.controls.period.value === 'custom') {
            <div class="grid gap-3 sm:grid-cols-2">
              <div>
                <label class="mb-1 block">Period start</label>
                <input class="input-field" type="date" formControlName="period_start" />
              </div>
              <div>
                <label class="mb-1 block">Period end</label>
                <input class="input-field" type="date" formControlName="period_end" />
              </div>
            </div>
          }
          <div>
            <label class="mb-1 block">Description</label>
            <textarea class="input-field min-h-[80px]" formControlName="description"></textarea>
          </div>
          <div>
            <label class="mb-1 block">Notes</label>
            <textarea class="input-field min-h-[60px]" formControlName="notes"></textarea>
          </div>
          <div>
            <label class="mb-1 block">Target date</label>
            <input class="input-field" type="date" formControlName="target_date" />
          </div>
          <div>
            <label class="mb-1 block">Progress (%)</label>
            <input class="input-field" type="number" min="0" max="100" formControlName="progress" />
          </div>
          @if (error) {
            <p class="text-xs" style="color: var(--danger)">{{ error }}</p>
          }
          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">
              {{ saving ? 'Saving…' : 'Save' }}
            </button>
            <a routerLink="/goals" class="btn-secondary no-underline">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  `,
})
export class GoalFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly goalsService = inject(GoalsService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  categories = GOAL_CATEGORIES;
  periods = GOAL_PERIODS;
  isEdit = false;
  goalId: string | null = null;
  saving = false;
  error = '';

  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    category: ['personal' as GoalCategory, Validators.required],
    period: ['yearly' as GoalPeriod, Validators.required],
    description: [''],
    notes: [''],
    target_date: [''],
    period_start: [''],
    period_end: [''],
    progress: [0, [Validators.min(0), Validators.max(100)]],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.goalId = id;
      this.goalsService.get(id).subscribe({
        next: (goal) => {
          this.form.patchValue({
            title: goal.title,
            category: goal.category,
            period: goal.period || 'yearly',
            description: goal.description ?? '',
            notes: goal.notes ?? '',
            target_date: goal.target_date ? goal.target_date.slice(0, 10) : '',
            period_start: goal.period_start ? goal.period_start.slice(0, 10) : '',
            period_end: goal.period_end ? goal.period_end.slice(0, 10) : '',
            progress: goal.progress,
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
      title: raw.title,
      category: raw.category,
      period: raw.period,
      description: raw.description || null,
      notes: raw.notes || null,
      progress: raw.progress,
      target_date: raw.target_date ? new Date(raw.target_date).toISOString() : null,
      period_start: raw.period === 'custom' && raw.period_start ? raw.period_start : null,
      period_end: raw.period === 'custom' && raw.period_end ? raw.period_end : null,
    };

    const req = this.isEdit && this.goalId
      ? this.goalsService.update(this.goalId, payload)
      : this.goalsService.create(payload);

    req.subscribe({
      next: (goal) => {
        this.router.navigate(['/goals', goal.id]);
      },
      error: (err) => {
        this.error = err?.error?.detail || 'Failed to save goal';
        this.saving = false;
      },
    });
  }
}
