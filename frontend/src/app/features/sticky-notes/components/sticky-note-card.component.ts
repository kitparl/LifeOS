import { DatePipe } from '@angular/common';
import { CdkDragHandle } from '@angular/cdk/drag-drop';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { STICKY_NOTE_COLORS, StickyNote, daysUntilPurge, stickyNoteDisplayTitle } from '../models/sticky-note.models';

@Component({
  selector: 'app-sticky-note-card',
  standalone: true,
  imports: [DatePipe, CdkDragHandle, LucideDynamicIcon],
  template: `
    <div
      class="note-card group relative flex h-full min-h-[140px] flex-col gap-2 rounded-[var(--radius-lg)] border border-[var(--border)] p-3 shadow-[var(--shadow-sm)] transition-shadow hover:shadow-[var(--shadow-md)]"
      [style.background]="'var(--note-' + note.color + ')'"
    >
      <div class="flex items-start justify-between gap-2">
        @if (deletedMode) {
          <span class="min-w-0 flex-1 truncate text-sm font-medium text-[var(--text)]">{{ displayTitle() }}</span>
        } @else {
          <button
            type="button"
            class="min-w-0 flex-1 truncate text-left text-sm font-medium text-[var(--text)]"
            (click)="open.emit()"
          >
            {{ displayTitle() }}
          </button>
          @if (draggable) {
            <span cdkDragHandle class="cursor-grab shrink-0 text-[var(--text-faint)] opacity-0 transition-opacity group-hover:opacity-100" title="Drag to reorder" aria-hidden="true">⋮⋮</span>
          }
        }
      </div>

      @if (deletedMode) {
        <p class="min-h-0 flex-1 whitespace-pre-line text-xs text-[var(--text-muted)] line-clamp-6">{{ note.content }}</p>
      } @else {
        <button type="button" class="min-h-0 flex-1 cursor-text text-left text-xs whitespace-pre-line text-[var(--text-muted)] line-clamp-6" (click)="open.emit()">
          {{ note.content }}
        </button>
      }

      <div class="flex items-center justify-between gap-2 border-t border-[var(--border)] pt-2 text-[10px] text-[var(--text-faint)]">
        @if (deletedMode) {
          <span>Deleted — removed in {{ daysLeft() }} day{{ daysLeft() === 1 ? '' : 's' }}</span>
          <button
            type="button"
            class="flex items-center gap-1 rounded px-1.5 py-1 text-xs font-medium text-[var(--text)] hover:bg-[var(--surface-3)]"
            title="Restore note"
            aria-label="Restore note"
            (click)="restore.emit()"
          >
            <svg class="h-3.5 w-3.5" lucideIcon="rotate-ccw" aria-hidden="true"></svg>
            Restore
          </button>
        } @else {
          <span>{{ note.updated_at | date: 'MMM d, h:mm a' }}</span>
          <div class="flex items-center gap-1">
            <button
              type="button"
              class="rounded p-1 hover:bg-[var(--surface-3)]"
              [style.color]="note.is_pinned ? 'var(--primary)' : null"
              [attr.aria-pressed]="note.is_pinned"
              title="Pin note"
              aria-label="Pin note"
              (click)="togglePin.emit()"
            >
              <svg class="h-3.5 w-3.5" lucideIcon="pin" [attr.fill]="note.is_pinned ? 'currentColor' : 'none'" aria-hidden="true"></svg>
            </button>
            <div class="relative">
              <button
                type="button"
                class="rounded p-1 hover:bg-[var(--surface-3)]"
                title="Change color"
                aria-label="Change color"
                (click)="colorMenuOpen = !colorMenuOpen; $event.stopPropagation()"
              >
                <svg class="h-3.5 w-3.5" lucideIcon="palette" aria-hidden="true"></svg>
              </button>
              @if (colorMenuOpen) {
                <div class="absolute bottom-full right-0 z-10 mb-1 flex gap-1 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-1.5 shadow-[var(--shadow-md)]">
                  @for (c of colors; track c.value) {
                    <button
                      type="button"
                      class="h-4 w-4 rounded-full border border-[var(--border)]"
                      [style.background]="'var(--note-' + c.value + ')'"
                      [attr.aria-label]="c.label"
                      [title]="c.label"
                      (click)="setColor(c.value)"
                    ></button>
                  }
                </div>
              }
            </div>
            <button
              type="button"
              class="rounded p-1 hover:bg-[var(--danger-soft)] hover:text-[var(--danger)]"
              title="Delete note"
              aria-label="Delete note"
              (click)="deleteNote.emit()"
            >
              <svg class="h-3.5 w-3.5" lucideIcon="trash-2" aria-hidden="true"></svg>
            </button>
          </div>
        }
      </div>
    </div>
  `,
})
export class StickyNoteCardComponent {
  @Input({ required: true }) note!: StickyNote;
  @Input() draggable = true;
  /** Shows a "removed in N days" + Restore action instead of the normal pin/color/delete row. */
  @Input() deletedMode = false;

  @Output() open = new EventEmitter<void>();
  @Output() togglePin = new EventEmitter<void>();
  @Output() colorChange = new EventEmitter<StickyNote['color']>();
  @Output() deleteNote = new EventEmitter<void>();
  @Output() restore = new EventEmitter<void>();

  readonly colors = STICKY_NOTE_COLORS;
  colorMenuOpen = false;

  displayTitle(): string {
    return stickyNoteDisplayTitle(this.note);
  }

  daysLeft(): number {
    return daysUntilPurge(this.note.deleted_at);
  }

  setColor(color: StickyNote['color']): void {
    this.colorMenuOpen = false;
    this.colorChange.emit(color);
  }
}
