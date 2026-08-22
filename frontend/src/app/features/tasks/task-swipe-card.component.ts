import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TaskListItem } from './models/task.models';

@Component({
  selector: 'app-task-swipe-card',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <div
      class="task-swipe-wrap"
      [class.task-swipe-wrap--swiping]="swiping"
      (touchstart)="onTouchStart($event)"
      (touchmove)="onTouchMove($event)"
      (touchend)="onTouchEnd($event)"
    >
      <div class="task-swipe-done" [class.task-swipe-done--show]="offsetX > 24">Done</div>
      <article class="task-card" [style.transform]="offsetX ? 'translateX(' + offsetX + 'px)' : null">
        <div class="task-card__row">
          <div class="task-card__main min-w-0 flex-1">
            <a [routerLink]="['/tasks', task.id]" class="link font-medium leading-snug">{{ task.title }}</a>
            <div class="mt-1 flex flex-wrap items-center gap-1 text-xs" style="color: var(--text-muted)">
              @if (isOverdue) {
                <span class="chip" style="color: var(--warning, #b45309)">Overdue</span>
              } @else if (task.due_date) {
                <span>{{ task.due_date | date: 'mediumDate' }}</span>
              } @else {
                <span>No date</span>
              }
            </div>
          </div>
          @if (task.status !== 'completed') {
            <div class="task-card__actions shrink-0 flex flex-wrap justify-end gap-1">
              @if (showTodayAction) {
                <button type="button" class="btn-ghost px-2 text-xs" (click)="scheduleToday.emit(task.id)">Today</button>
              }
              @if (showDateAction) {
                <button type="button" class="btn-ghost px-2 text-xs" (click)="scheduleDate.emit(task.id)">Date</button>
              }
              <button type="button" class="btn-primary px-2 text-xs" (click)="complete.emit(task.id)">Done</button>
            </div>
          }
        </div>
      </article>
    </div>
  `,
  styles: [
    `
      .task-swipe-wrap {
        position: relative;
        overflow: hidden;
        border-radius: 0.5rem;
      }
      .task-swipe-wrap--swiping .task-card {
        transition: none;
      }
      .task-swipe-done {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        padding-left: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: #fff;
        background: var(--primary, #0066cc);
        opacity: 0;
      }
      .task-swipe-done--show {
        opacity: 1;
      }
      .task-card {
        position: relative;
        border: 1px solid var(--xp-border);
        border-radius: 0.5rem;
        background: var(--surface-1, #fff);
        transition: transform 0.15s ease-out;
        touch-action: pan-y;
      }
      .task-card__row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.625rem 0.75rem;
      }
      .task-card__actions {
        max-width: 9rem;
      }
      @media (max-width: 767px) {
        .task-card__actions .btn-ghost {
          display: none;
        }
      }
    `,
  ],
})
export class TaskSwipeCardComponent {
  @Input({ required: true }) task!: TaskListItem;
  @Input() showTodayAction = false;
  @Input() showDateAction = false;
  @Input() isOverdue = false;

  @Output() complete = new EventEmitter<string>();
  @Output() scheduleToday = new EventEmitter<string>();
  @Output() scheduleDate = new EventEmitter<string>();

  offsetX = 0;
  swiping = false;
  private startX = 0;
  private startY = 0;
  private tracking = false;
  private horizontal = false;

  onTouchStart(event: TouchEvent): void {
    if (this.task.status === 'completed' || event.touches.length !== 1) {
      return;
    }
    this.startX = event.touches[0].clientX;
    this.startY = event.touches[0].clientY;
    this.tracking = true;
    this.horizontal = false;
    this.swiping = false;
  }

  onTouchMove(event: TouchEvent): void {
    if (!this.tracking) {
      return;
    }
    const dx = event.touches[0].clientX - this.startX;
    const dy = event.touches[0].clientY - this.startY;
    if (!this.horizontal) {
      if (Math.abs(dx) < 8 && Math.abs(dy) < 8) {
        return;
      }
      this.horizontal = Math.abs(dx) > Math.abs(dy);
      if (!this.horizontal) {
        this.tracking = false;
        return;
      }
    }
    if (dx > 0) {
      this.swiping = true;
      this.offsetX = Math.min(dx, 120);
      event.preventDefault();
    }
  }

  onTouchEnd(event: TouchEvent): void {
    if (!this.tracking) {
      return;
    }
    const dx = event.changedTouches[0].clientX - this.startX;
    if (this.horizontal && dx > 72) {
      this.complete.emit(this.task.id);
    }
    this.offsetX = 0;
    this.swiping = false;
    this.tracking = false;
    this.horizontal = false;
  }
}
