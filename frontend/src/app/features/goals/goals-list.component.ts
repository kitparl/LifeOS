import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ListPaginatorComponent } from '../../shared/pagination/list-paginator.component';
import { GOAL_CATEGORIES, GoalListItem } from './models/goal.models';
import { GoalsService } from './services/goals.service';

@Component({
  selector: 'app-goals-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe, ListPaginatorComponent],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Goals</h1>
        <a routerLink="/goals/new" class="btn-primary text-xs no-underline">New Goal</a>
      </div>

      <form class="flex flex-wrap gap-2 text-sm" [formGroup]="filters" (ngSubmit)="applyFilters()">
        <select class="input-field !w-auto" formControlName="category">
          <option value="">All categories</option>
          @for (c of categories; track c.value) {
            <option [value]="c.value">{{ c.label }}</option>
          }
        </select>
        <select class="input-field !w-auto" formControlName="status">
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="archived">Archived</option>
          <option value="completed">Completed</option>
        </select>
        <button type="submit" class="btn-primary text-xs">Filter</button>
      </form>

      @if (loading) {
        <p class="text-sm" style="color: var(--text-muted)">Loading goals…</p>
      } @else if (goals.length === 0) {
        <div class="panel">
          <p class="text-sm" style="color: var(--text-muted)">No goals yet.</p>
          <a routerLink="/goals/new" class="btn-primary mt-2 inline-block text-xs no-underline">Create your first goal</a>
        </div>
      } @else {
        <div class="space-y-3 md:hidden">
          @for (goal of pagedGoals; track goal.id) {
            <article class="panel space-y-3">
              <div class="min-w-0">
                <a [routerLink]="['/goals', goal.id]" class="block truncate text-sm font-semibold text-[var(--xp-blue)] underline">
                  {{ goal.title }}
                </a>
                <p class="mt-1 text-xs capitalize text-[var(--text-muted)]">
                  {{ goal.category }} · {{ goal.status }} · {{ goal.updated_at | date: 'mediumDate' }}
                </p>
              </div>
              <div class="flex items-center gap-2">
                <div class="h-2 flex-1 rounded-full bg-[var(--surface-3)]">
                  <div class="h-full rounded-full bg-[var(--xp-blue)]" [style.width.%]="goal.progress"></div>
                </div>
                <span class="text-xs font-semibold">{{ goal.progress }}%</span>
              </div>
            </article>
          }
          <app-list-paginator
            [total]="goals.length"
            [pageSize]="pageSize"
            [currentPage]="currentPage"
            (pageChange)="setPage($event)"
          />
        </div>
        <div class="panel hidden !p-0 overflow-hidden md:block">
          <table class="w-full text-sm">
            <thead class="border-b border-[var(--xp-border)] bg-[var(--xp-silver)] text-left">
              <tr>
                <th class="px-3 py-2">Title</th>
                <th class="px-3 py-2">Category</th>
                <th class="px-3 py-2">Progress</th>
                <th class="px-3 py-2">Status</th>
                <th class="px-3 py-2">Updated</th>
              </tr>
            </thead>
            <tbody>
              @for (goal of pagedGoals; track goal.id) {
                <tr class="border-b border-[var(--xp-border)] hover:bg-[var(--primary-soft)]">
                  <td class="px-3 py-2">
                    <a [routerLink]="['/goals', goal.id]" class="link">{{ goal.title }}</a>
                  </td>
                  <td class="px-3 py-2 capitalize">{{ goal.category }}</td>
                  <td class="px-3 py-2">
                    <div class="flex items-center gap-2">
                      <div class="h-2 w-20 bg-gray-200 border border-[var(--xp-border)]">
                        <div class="h-full bg-[var(--xp-blue)]" [style.width.%]="goal.progress"></div>
                      </div>
                      <span class="text-xs">{{ goal.progress }}%</span>
                    </div>
                  </td>
                  <td class="px-3 py-2 capitalize">{{ goal.status }}</td>
                  <td class="px-3 py-2 text-xs text-gray-600">{{ goal.updated_at | date: 'medium' }}</td>
                </tr>
              }
            </tbody>
          </table>
          <app-list-paginator
            [total]="goals.length"
            [pageSize]="pageSize"
            [currentPage]="currentPage"
            (pageChange)="setPage($event)"
          />
        </div>
      }
    </div>
  `,
})
export class GoalsListComponent implements OnInit {
  private readonly goalsService = inject(GoalsService);
  private readonly fb = inject(FormBuilder);

  categories = GOAL_CATEGORIES;
  goals: GoalListItem[] = [];
  loading = false;
  currentPage = 1;
  readonly pageSize = 12;

  filters = this.fb.nonNullable.group({ category: '', status: 'active' });

  ngOnInit(): void {
    this.load();
  }

  get pagedGoals(): GoalListItem[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.goals.slice(start, start + this.pageSize);
  }

  applyFilters(): void {
    this.currentPage = 1;
    this.load();
  }

  load(): void {
    this.loading = true;
    const { category, status } = this.filters.getRawValue();
    this.goalsService.list(category || undefined, status || undefined).subscribe({
      next: (data) => {
        this.goals = data;
        this.clampPage();
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }

  setPage(page: number): void {
    this.currentPage = page;
  }

  private clampPage(): void {
    const totalPages = Math.max(1, Math.ceil(this.goals.length / this.pageSize));
    this.currentPage = Math.min(this.currentPage, totalPages);
  }
}
