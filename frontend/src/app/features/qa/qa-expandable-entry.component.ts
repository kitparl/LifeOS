import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { QAListItem } from './models/qa.models';

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
          <a [routerLink]="['/qa', entry.id, 'edit']" class="mt-2 inline-block text-xs underline">Edit</a>
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

  @Output() toggle = new EventEmitter<string>();

  get dateValue(): string {
    return this.dateField === 'created_at' ? this.entry.created_at : this.entry.updated_at;
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
