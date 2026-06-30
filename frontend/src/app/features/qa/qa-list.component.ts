import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { QAListItem } from './models/qa.models';
import { QAService } from './services/qa.service';

@Component({
  selector: 'app-qa-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe],
  template: `
    <div class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Personal Q&A</h1>
        <a routerLink="/qa/new" class="btn-primary text-xs no-underline">New Q&A</a>
      </div>

      <form class="flex gap-2 text-sm" [formGroup]="filters" (ngSubmit)="load()">
        <input class="input-field !w-48" formControlName="search" placeholder="Search…" />
        <button type="submit" class="btn-primary text-xs">Filter</button>
      </form>

      @if (loading) {
        <p class="text-sm text-gray-600">Loading…</p>
      } @else if (entries.length === 0) {
        <div class="panel">
          <p class="text-sm text-gray-600">No Q&A entries yet.</p>
          <a routerLink="/qa/new" class="btn-primary mt-2 inline-block text-xs no-underline">Create one</a>
        </div>
      } @else {
        <div class="panel !p-0 overflow-hidden">
          <table class="w-full text-sm">
            <thead class="border-b border-[var(--xp-border)] bg-[#e8e8e8] text-left">
              <tr>
                <th class="px-3 py-2">Question</th>
                <th class="px-3 py-2">Tags</th>
                <th class="px-3 py-2">Updated</th>
                <th class="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              @for (entry of entries; track entry.id) {
                <tr class="border-b border-[var(--xp-border)] hover:bg-[#d6e4f7]">
                  <td class="px-3 py-2 max-w-md">
                    <a [routerLink]="['/qa', entry.id]" class="text-[var(--xp-blue)] underline">{{ entry.question }}</a>
                  </td>
                  <td class="px-3 py-2 text-xs text-gray-600">{{ entry.tags.join(', ') || '—' }}</td>
                  <td class="px-3 py-2 text-xs">{{ entry.updated_at | date: 'mediumDate' }}</td>
                  <td class="px-3 py-2">
                    <a [routerLink]="['/qa', entry.id, 'edit']" class="text-xs underline">Edit</a>
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
export class QAListComponent implements OnInit {
  private readonly qaService = inject(QAService);
  private readonly fb = inject(FormBuilder);

  entries: QAListItem[] = [];
  loading = false;
  filters = this.fb.nonNullable.group({ search: '' });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    const search = this.filters.getRawValue().search;
    this.qaService.list(search || undefined).subscribe({
      next: (data) => {
        this.entries = data;
        this.loading = false;
      },
      error: () => (this.loading = false),
    });
  }
}
