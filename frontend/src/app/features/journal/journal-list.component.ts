import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { JOURNAL_TYPES, JournalListItem } from './models/journal.models';
import { JournalService } from './services/journal.service';

@Component({
  selector: 'app-journal-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Journal</h1>
        <a routerLink="/journal/new" class="btn-primary text-xs no-underline">New Entry</a>
      </div>

      <form class="flex flex-wrap gap-2 text-sm" [formGroup]="filters" (ngSubmit)="load()">
        <select class="input-field !w-auto" formControlName="entry_type">
          <option value="">All types</option>
          @for (t of types; track t.value) {
            <option [value]="t.value">{{ t.label }}</option>
          }
        </select>
        <input class="input-field !w-40" formControlName="search" placeholder="Search…" />
        <button type="submit" class="btn-primary text-xs">Filter</button>
      </form>

      @if (loading) {
        <p class="text-sm text-gray-600">Loading entries…</p>
      } @else if (entries.length === 0) {
        <div class="panel">
          <p class="text-sm text-gray-600">No journal entries yet.</p>
          <a routerLink="/journal/new" class="btn-primary mt-2 inline-block text-xs no-underline">Write entry</a>
        </div>
      } @else {
        <div class="panel !p-0 overflow-hidden">
          <table class="w-full text-sm">
            <thead class="border-b border-[var(--xp-border)] bg-[#e8e8e8] text-left">
              <tr>
                <th class="px-3 py-2">Date</th>
                <th class="px-3 py-2">Type</th>
                <th class="px-3 py-2">Preview</th>
                <th class="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              @for (entry of entries; track entry.id) {
                <tr class="border-b border-[var(--xp-border)] hover:bg-[#d6e4f7]">
                  <td class="px-3 py-2">{{ entry.entry_date | date: 'mediumDate' }}</td>
                  <td class="px-3 py-2 capitalize">{{ entry.entry_type }}</td>
                  <td class="px-3 py-2 max-w-xs truncate">
                    <a [routerLink]="['/journal', entry.id]" class="text-[var(--xp-blue)] underline">
                      {{ entry.title || entry.content || '—' }}
                    </a>
                  </td>
                  <td class="px-3 py-2">
                    <a [routerLink]="['/journal', entry.id, 'edit']" class="text-xs underline">Edit</a>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
  `,
})
export class JournalListComponent implements OnInit {
  private readonly journalService = inject(JournalService);
  private readonly fb = inject(FormBuilder);

  types = JOURNAL_TYPES;
  entries: JournalListItem[] = [];
  loading = false;

  filters = this.fb.nonNullable.group({ entry_type: '', search: '' });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    const raw = this.filters.getRawValue();
    this.journalService
      .list(raw.entry_type || undefined, raw.search || undefined)
      .subscribe({
        next: (data) => {
          this.entries = data;
          this.loading = false;
        },
        error: () => (this.loading = false),
      });
  }
}
