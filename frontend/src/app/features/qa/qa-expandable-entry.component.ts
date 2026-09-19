import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { QAListItem, qaDaysUntilPurge } from './models/qa.models';

@Component({
  selector: 'app-qa-expandable-entry',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    <article class="panel space-y-2">
      <button type="button" class="w-full text-left" (click)="toggle.emit(entry.id)">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0 flex-1">
            @if (showDayPrefix) {
              <p class="text-xs font-medium" style="color: var(--text-muted)">
                {{ entry.created_at | date: 'MMM d' }}
              </p>
            }
            <p class="text-sm font-semibold">{{ entry.question }}</p>
            <p class="mt-1 flex flex-wrap items-center gap-2 text-xs" style="color: var(--text-muted)">
              @if (entry.type) {
                <span class="qa-type-badge">{{ entry.type }}</span>
              }
              @if (entry.tags.length) {
                <span>{{ entry.tags.join(' · ') }}</span>
              }
              @if (!showDayPrefix && showDate) {
                <span>{{ dateValue | date: dateFormat }}</span>
              }
              @if (deletedMode) {
                <span>Deletes in {{ daysLeft }}d</span>
              }
            </p>
          </div>
          <span class="shrink-0 text-xs" aria-hidden="true">{{ expanded ? '▲' : '▼' }}</span>
        </div>
      </button>
      @if (expanded) {
        <div class="border-t border-[var(--xp-border)] pt-2 text-sm">
          @if (loadingAnswer) {
            <p class="text-xs" style="color: var(--text-muted)">Loading answer…</p>
          } @else {
            <p class="whitespace-pre-wrap">{{ answer || 'No answer yet.' }}</p>
          }
          <p class="mt-2 text-xs" style="color: var(--text-muted)">
            Tags: {{ entry.tags.join(', ') || '—' }}
          </p>
          <div class="mt-2 flex items-center gap-3">
            @if (deletedMode) {
              <button type="button" class="text-xs underline" (click)="onRestore($event)">
                Restore
              </button>
            } @else {
              <a [routerLink]="['/qa', entry.id, 'edit']" class="text-xs underline">Edit</a>
              <button
                type="button"
                class="text-xs underline"
                style="color: var(--danger)"
                (click)="onRemove($event)"
              >
                Delete
              </button>
            }
          </div>
        </div>
      }
    </article>
  `,
})
export class QAExpandableEntryComponent {
  @Input({ required: true }) entry!: QAListItem;
  @Input() expanded = false;
  @Input() answer: string | null = null;
  @Input() loadingAnswer = false;
  @Input() showDayPrefix = false;
  @Input() showDate = true;
  @Input() dateField: 'created_at' | 'updated_at' = 'updated_at';
  @Input() dateFormat = 'mediumDate';
  @Input() deletedMode = false;

  @Output() toggle = new EventEmitter<string>();
  @Output() remove = new EventEmitter<string>();
  @Output() restore = new EventEmitter<string>();

  get dateValue(): string {
    return this.dateField === 'created_at' ? this.entry.created_at : this.entry.updated_at;
  }

  get daysLeft(): number {
    return qaDaysUntilPurge(this.entry.deleted_at);
  }

  onRemove(event: Event): void {
    event.stopPropagation();
    this.remove.emit(this.entry.id);
  }

  onRestore(event: Event): void {
    event.stopPropagation();
    this.restore.emit(this.entry.id);
  }
}

export function monthGroupKey(isoDate: string): string {
  const d = new Date(isoDate);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

export function monthGroupLabel(isoDate: string): string {
  const d = new Date(isoDate);
  return d.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
}

export interface MonthGroup {
  key: string;
  label: string;
  entries: import('./models/qa.models').QAListItem[];
}

export function groupEntriesByMonth(
  entries: import('./models/qa.models').QAListItem[],
): MonthGroup[] {
  const groups = new Map<string, MonthGroup>();
  for (const entry of entries) {
    const key = monthGroupKey(entry.created_at);
    const existing = groups.get(key);
    if (existing) {
      existing.entries.push(entry);
    } else {
      groups.set(key, {
        key,
        label: monthGroupLabel(entry.created_at),
        entries: [entry],
      });
    }
  }
  return Array.from(groups.values());
}
