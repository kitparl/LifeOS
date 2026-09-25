import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ListPaginatorComponent } from '../../shared/pagination/list-paginator.component';
import { TaskListItem } from './models/task.models';
import { TaskSwipeCardComponent } from './task-swipe-card.component';

@Component({
  selector: 'app-task-list-section',
  standalone: true,
  imports: [ListPaginatorComponent, TaskSwipeCardComponent],
  template: `
    <section
      class="task-board-section"
      [class.task-board-section--today]="variant === 'today'"
      [class.task-board-section--overdue]="variant === 'overdue'"
    >
      @if (showHead) {
        <div class="task-board-section__head">
          <h2 class="task-board-section__title">{{ title }}</h2>
          @if (hint) {
            <p class="task-board-section__hint">{{ hint }}</p>
          }
        </div>
      }

      <div class="task-board-section__body panel !p-2">
        @if (loading) {
          <p class="px-2 py-3 text-sm" style="color: var(--text-muted)" role="status">Loading…</p>
        } @else if (error) {
          <div class="px-2 py-4 text-center" role="alert">
            <p class="text-sm" style="color: var(--danger)">Couldn't load tasks.</p>
            <button type="button" class="btn-secondary mt-2 text-xs" (click)="retry.emit()">Try again</button>
          </div>
        } @else if (tasks.length === 0) {
          <div class="px-2 py-4 text-center">
            <p class="text-sm" style="color: var(--text-muted)">{{ emptyMessage }}</p>
            <ng-content select="[emptyAction]" />
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
        align-items: baseline;
        flex-wrap: wrap;
        gap: 0 0.5rem;
        margin-bottom: 0.5rem;
      }
      .task-board-section__title {
        font-size: 0.875rem;
        font-weight: 600;
      }
      .task-board-section__hint {
        font-size: 0.75rem;
        color: var(--text-muted);
      }
      .task-board-section--today .task-board-section__body {
        border: 1px solid var(--xp-border);
        background: var(--primary-soft);
      }
      .task-board-section--overdue .task-board-section__title {
        color: var(--warning);
      }
      .task-board-section--overdue .task-board-section__body {
        border-color: color-mix(in srgb, var(--warning) 35%, var(--xp-border));
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
  @Input() pageSize = 25;
  @Input() currentPage = 1;
  @Input() loading = false;
  @Input() error = false;
  @Input() emptyMessage = 'No tasks.';
  /** Hide the heading when the surrounding view already names the list. */
  @Input() showHead = true;

  @Output() pageChange = new EventEmitter<number>();
  @Output() complete = new EventEmitter<string>();
  @Output() scheduleToday = new EventEmitter<string>();
  @Output() scheduleDate = new EventEmitter<string>();
  @Output() retry = new EventEmitter<void>();
}
