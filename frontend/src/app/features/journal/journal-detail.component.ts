import { DatePipe, TitleCasePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MarkdownPipe } from '../../shared/markdown/markdown.pipe';
import { JournalEntry } from './models/journal.models';
import { JournalService } from './services/journal.service';

@Component({
  selector: 'app-journal-detail',
  standalone: true,
  imports: [RouterLink, DatePipe, TitleCasePipe, MarkdownPipe],
  template: `
    @if (entry; as e) {
      <div class="journal-writer space-y-4">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 class="text-2xl font-bold">{{ e.title || (e.entry_type | titlecase) + ' Journal' }}</h1>
            <p class="text-xs" style="color: var(--text-muted)">
              {{ e.entry_date | date: 'fullDate' }} · {{ e.entry_type }}
            </p>
          </div>
          <div class="flex gap-2">
            <a [routerLink]="['/journal', e.id, 'edit']" class="btn-primary text-xs no-underline">Edit</a>
            <button type="button" class="btn-danger text-xs" (click)="remove()">Delete</button>
          </div>
        </div>

        <div class="markdown-body" [innerHTML]="e.content | markdown"></div>

        @if (e.gratitude) {
          <div class="journal-section">
            <p class="journal-section__label">Gratitude</p>
            <div class="markdown-body" [innerHTML]="e.gratitude | markdown"></div>
          </div>
        }
        @if (e.wins) {
          <div class="journal-section">
            <p class="journal-section__label">Wins</p>
            <div class="markdown-body" [innerHTML]="e.wins | markdown"></div>
          </div>
        }
        @if (e.lessons) {
          <div class="journal-section">
            <p class="journal-section__label">Lessons Learned</p>
            <div class="markdown-body" [innerHTML]="e.lessons | markdown"></div>
          </div>
        }

        <a routerLink="/journal" class="link text-sm">Back to journal</a>
      </div>
    } @else if (loading) {
      <p class="text-sm">Loading entry…</p>
    } @else {
      <p class="text-sm" style="color: var(--danger)">Entry not found.</p>
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
