import { Component, EventEmitter, Input, Output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ListPaginatorComponent } from '../../shared/pagination/list-paginator.component';
import { TaskListItem } from './models/task.models';
import { TaskSwipeCardComponent } from './task-swipe-card.component';

@Component({
  selector: 'app-task-list-section',
  standalone: true,
  imports: [RouterLink, ListPaginatorComponent, TaskSwipeCardComponent],
  template: `
    <section
      class="task-board-section"
      [class.task-board-section--today]="variant === 'today'"
      [class.task-board-section--overdue]="variant === 'overdue'"
    >
      <div class="task-board-section__head">
        <div>
          <h2 class="task-board-section__title">{{ title }}</h2>
          @if (hint) {
            <p class="task-board-section__hint">{{ hint }}</p>
          }
        </div>
        @if (total > 0) {
          <span class="chip text-xs">{{ total }}</span>
        }
      </div>

      <div class="task-board-section__body panel !p-2">
        @if (loading) {
          <p class="px-2 py-3 text-sm" style="color: var(--text-muted)">Loading…</p>
        } @else if (tasks.length === 0) {
          <div class="px-2 py-4 text-center">
            <p class="text-sm" style="color: var(--text-muted)">{{ emptyMessage }}</p>
            @if (showCreateLink) {
              <a routerLink="/tasks/new" class="btn-primary mt-2 inline-block text-xs no-underline">Create task</a>
            }
          </div>
        } @else {
          <ul class="space-y-1.5">
            @for (task of tasks; track task.id) {
              <li>
                <app-task-swipe-card
                  [task]="task"
                  [showTodayAction]="showTodayAction"
                  [showDateAction]="showDateAction"
                  [isOverdue]="variant === 'overdue'"
                  (complete)="complete.emit($event)"
                  (scheduleToday)="scheduleToday.emit($event)"
                  (scheduleDate)="scheduleDate.emit($event)"
                />
              </li>
            }
          </ul>
        }
      </div>

      @if (!loading && total > pageSize) {
        <app-list-paginator
          [total]="total"
          [pageSize]="pageSize"
          [currentPage]="currentPage"
          (pageChange)="pageChange.emit($event)"
        />
      }
    </section>
  `,
  styles: [
    `
      .task-board-section__head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
      }
      .task-board-section__title {
        font-size: 0.875rem;
        font-weight: 600;
      }
      .task-board-section__hint {
        margin-top: 0.125rem;
        font-size: 0.75rem;
        color: var(--text-muted);
      }
      .task-board-section--today .task-board-section__body {
        border: 1px solid var(--xp-border);
        background: var(--primary-soft);
      }
      .task-board-section--overdue .task-board-section__body {
        border-color: color-mix(in srgb, var(--warning, #b45309) 35%, var(--xp-border));
      }
    `,
  ],
})
export class TaskListSectionComponent {
  @Input({ required: true }) title!: string;
  @Input() hint = '';
  @Input() variant: 'today' | 'overdue' | 'nodate' | 'upcoming' = 'nodate';
  @Input() showTodayAction = false;
  @Input() showDateAction = false;
  @Input() tasks: TaskListItem[] = [];
  @Input() total = 0;
  @Input() pageSize = 12;
  @Input() currentPage = 1;
  @Input() loading = false;
  @Input() emptyMessage = 'No tasks.';
  @Input() showCreateLink = false;

  @Output() pageChange = new EventEmitter<number>();
  @Output() complete = new EventEmitter<string>();
  @Output() scheduleToday = new EventEmitter<string>();
  @Output() scheduleDate = new EventEmitter<string>();
}
