import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { GoalProgressItem } from '../models/dashboard.models';
import { WidgetSkeletonComponent } from './widget-skeleton.component';

@Component({
  selector: 'app-goals-widget',
  standalone: true,
  imports: [RouterLink, WidgetSkeletonComponent],
  template: `
    <div class="panel !p-0 overflow-hidden h-full">
      <div class="title-bar rounded-none border-x-0 border-t-0 flex justify-between">
        <span>Goal Progress</span>
        <a routerLink="/goals" class="text-xs font-normal underline opacity-90">View all</a>
      </div>
      @if (loading) {
        <app-widget-skeleton />
      } @else if (goals.length === 0) {
        <div class="p-3 text-sm text-gray-600">
          <p>No active goals</p>
          <a routerLink="/goals/new" class="btn-primary mt-2 inline-block text-xs no-underline">Add goal</a>
        </div>
      } @else {
        <ul class="space-y-2 p-3 text-sm">
          @for (goal of goals; track goal.id) {
            <li>
              <a [routerLink]="['/goals', goal.id]" class="flex justify-between mb-1 no-underline text-inherit hover:underline">
                <span>{{ goal.title }}</span>
                <span class="text-xs">{{ goal.percent }}%</span>
              </a>
              <div class="h-2 bg-gray-200 border border-[var(--xp-border)]">
                <div class="h-full bg-[var(--xp-blue)]" [style.width.%]="goal.percent"></div>
              </div>
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class GoalsWidgetComponent {
  @Input() loading = false;
  @Input() goals: GoalProgressItem[] = [];
}
