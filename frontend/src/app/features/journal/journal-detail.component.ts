import { DatePipe, TitleCasePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { JournalEntry } from './models/journal.models';
import { JournalService } from './services/journal.service';

@Component({
  selector: 'app-journal-detail',
  standalone: true,
  imports: [RouterLink, DatePipe, TitleCasePipe],
  template: `
    @if (entry; as e) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 class="text-lg font-semibold">{{ e.title || (e.entry_type | titlecase) + ' Journal' }}</h1>
            <p class="text-xs text-gray-600">{{ e.entry_date | date: 'fullDate' }} · {{ e.entry_type }}</p>
          </div>
          <div class="flex gap-2">
            <a [routerLink]="['/journal', e.id, 'edit']" class="btn-primary text-xs no-underline">Edit</a>
            <button type="button" class="input-field !w-auto text-xs text-red-700" (click)="remove()">Delete</button>
          </div>
        </div>

        <div class="panel text-sm">
          <p class="font-medium mb-1">Content</p>
          <p class="whitespace-pre-wrap text-gray-700">{{ e.content }}</p>
        </div>

        @if (e.gratitude) {
          <div class="panel text-sm">
            <p class="font-medium mb-1">Gratitude</p>
            <p class="whitespace-pre-wrap text-gray-700">{{ e.gratitude }}</p>
          </div>
        }
        @if (e.wins) {
          <div class="panel text-sm">
            <p class="font-medium mb-1">Wins</p>
            <p class="whitespace-pre-wrap text-gray-700">{{ e.wins }}</p>
          </div>
        }
        @if (e.lessons) {
          <div class="panel text-sm">
            <p class="font-medium mb-1">Lessons</p>
            <p class="whitespace-pre-wrap text-gray-700">{{ e.lessons }}</p>
          </div>
        }

        <a routerLink="/journal" class="text-sm text-[var(--xp-blue)] underline">Back to journal</a>
      </div>
    } @else if (loading) {
      <p class="text-sm">Loading entry…</p>
    } @else {
      <p class="text-sm text-red-700">Entry not found.</p>
    }
  `,
})
export class JournalDetailComponent implements OnInit {
  private readonly journalService = inject(JournalService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  entry: JournalEntry | null = null;
  loading = false;

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) this.load(id);
  }

  load(id: string): void {
    this.loading = true;
    this.journalService.get(id).subscribe({
      next: (e) => {
        this.entry = e;
        this.loading = false;
      },
      error: () => {
        this.entry = null;
        this.loading = false;
      },
    });
  }

  remove(): void {
    if (!this.entry || !confirm('Delete this journal entry permanently?')) return;
    this.journalService.delete(this.entry.id).subscribe({
      next: () => this.router.navigate(['/journal']),
    });
  }
}
