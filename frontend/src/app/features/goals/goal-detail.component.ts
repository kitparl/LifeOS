import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Goal } from './models/goal.models';
import { GoalsService } from './services/goals.service';

@Component({
  selector: 'app-goal-detail',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe],
  template: `
    @if (goal; as g) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 class="text-lg font-semibold">{{ g.title }}</h1>
            <p class="text-xs capitalize text-gray-600">{{ g.category }} · {{ g.status }}</p>
          </div>
          <div class="flex gap-2">
            <a [routerLink]="['/goals', g.id, 'edit']" class="btn-primary text-xs no-underline">Edit</a>
            @if (g.status === 'active') {
              <button type="button" class="input-field !w-auto text-xs" (click)="archive()">Archive</button>
            }
            <button type="button" class="input-field !w-auto text-xs text-red-700" (click)="remove()">Delete</button>
          </div>
        </div>

        <div class="grid gap-3 md:grid-cols-2">
          <div class="panel !p-0 overflow-hidden">
            <div class="title-bar rounded-none border-x-0 border-t-0">Progress</div>
            <div class="p-3 text-sm space-y-2">
              <div class="h-3 bg-gray-200 border border-[var(--xp-border)]">
                <div class="h-full bg-[var(--xp-blue)]" [style.width.%]="g.progress"></div>
              </div>
              <p>{{ g.progress }}% complete</p>
              @if (g.target_date) {
                <p class="text-xs text-gray-600">Target: {{ g.target_date | date: 'mediumDate' }}</p>
              }
            </div>
          </div>

          <div class="panel !p-0 overflow-hidden">
            <div class="title-bar rounded-none border-x-0 border-t-0">Notes</div>
            <div class="p-3 text-sm">
              @if (g.notes) {
                <p class="whitespace-pre-wrap">{{ g.notes }}</p>
              } @else {
                <p class="text-gray-600">No notes</p>
              }
            </div>
          </div>
        </div>

        @if (g.description) {
          <div class="panel text-sm">
            <p class="font-medium mb-1">Description</p>
            <p class="whitespace-pre-wrap text-gray-700">{{ g.description }}</p>
          </div>
        }

        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Milestones</div>
          <div class="p-3 space-y-2">
            <form class="flex gap-2" [formGroup]="milestoneForm" (ngSubmit)="addMilestone()">
              <input class="input-field flex-1" formControlName="title" placeholder="New milestone…" />
              <button type="submit" class="btn-primary text-xs" [disabled]="milestoneForm.invalid">Add</button>
            </form>
            @if (g.milestones.length === 0) {
              <p class="text-sm text-gray-600">No milestones yet. Add one to track progress.</p>
            } @else {
              <ul class="divide-y divide-[var(--xp-border)] text-sm">
                @for (m of g.milestones; track m.id) {
                  <li class="flex items-center justify-between gap-2 py-2">
                    <label class="flex items-center gap-2">
                      <input
                        type="checkbox"
                        [checked]="m.completed"
                        (change)="toggleMilestone(m.id, $event)"
                      />
                      <span [class.line-through]="m.completed">{{ m.title }}</span>
                    </label>
                    <button type="button" class="text-xs text-red-700" (click)="deleteMilestone(m.id)">Remove</button>
                  </li>
                }
              </ul>
            }
          </div>
        </div>

        <a routerLink="/goals" class="text-sm text-[var(--xp-blue)] underline">Back to goals</a>
      </div>
    } @else if (loading) {
      <p class="text-sm">Loading goal…</p>
    } @else {
      <p class="text-sm text-red-700">Goal not found.</p>
    }
  `,
})
export class GoalDetailComponent implements OnInit {
  private readonly goalsService = inject(GoalsService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);

  goal: Goal | null = null;
  loading = false;

  milestoneForm = this.fb.nonNullable.group({ title: [''] });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) this.load(id);
  }

  load(id: string): void {
    this.loading = true;
    this.goalsService.get(id).subscribe({
      next: (g) => {
        this.goal = g;
        this.loading = false;
      },
      error: () => {
        this.goal = null;
        this.loading = false;
      },
    });
  }

  addMilestone(): void {
    if (!this.goal || this.milestoneForm.invalid) return;
    const title = this.milestoneForm.getRawValue().title.trim();
    if (!title) return;
    this.goalsService.addMilestone(this.goal.id, title).subscribe({
      next: () => {
        this.milestoneForm.reset({ title: '' });
        this.load(this.goal!.id);
      },
    });
  }

  toggleMilestone(milestoneId: string, event: Event): void {
    if (!this.goal) return;
    const checked = (event.target as HTMLInputElement).checked;
    this.goalsService.updateMilestone(this.goal.id, milestoneId, { completed: checked }).subscribe({
      next: () => this.load(this.goal!.id),
    });
  }

  deleteMilestone(milestoneId: string): void {
    if (!this.goal) return;
    this.goalsService.deleteMilestone(this.goal.id, milestoneId).subscribe({
      next: () => this.load(this.goal!.id),
    });
  }

  archive(): void {
    if (!this.goal) return;
    this.goalsService.archive(this.goal.id).subscribe({
      next: () => this.load(this.goal!.id),
    });
  }

  remove(): void {
    if (!this.goal || !confirm('Delete this goal permanently?')) return;
    this.goalsService.delete(this.goal.id).subscribe({
      next: () => this.router.navigate(['/goals']),
    });
  }
}
