import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { QAEntry } from './models/qa.models';
import { QAService } from './services/qa.service';

@Component({
  selector: 'app-qa-detail',
  standalone: true,
  imports: [RouterLink, DatePipe],
  template: `
    @if (entry; as e) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <h1 class="text-lg font-semibold">{{ e.question }}</h1>
          <div class="flex gap-2">
            <a [routerLink]="['/qa', e.id, 'edit']" class="btn-primary text-xs no-underline">Edit</a>
            <button type="button" class="input-field !w-auto text-xs text-red-700" (click)="remove()">Delete</button>
          </div>
        </div>

        @if (e.tags.length) {
          <p class="text-xs text-gray-600">Tags: {{ e.tags.join(', ') }}</p>
        }

        <div class="panel text-sm">
          <p class="font-medium mb-1">Current Answer</p>
          <p class="whitespace-pre-wrap text-gray-700">{{ e.current_answer }}</p>
        </div>

        @if (e.versions.length > 1) {
          <div class="panel !p-0 overflow-hidden">
            <div class="title-bar rounded-none border-x-0 border-t-0">Version History</div>
            <ul class="divide-y divide-[var(--xp-border)] text-sm">
              @for (v of e.versions; track v.id) {
                <li class="px-3 py-2">
                  <p class="text-xs text-gray-600 mb-1">v{{ v.version_number }} · {{ v.created_at | date: 'medium' }}</p>
                  <p class="whitespace-pre-wrap text-gray-700">{{ v.answer }}</p>
                </li>
              }
            </ul>
          </div>
        }

        <a routerLink="/qa" class="text-sm text-[var(--xp-blue)] underline">Back to Q&A</a>
      </div>
    } @else if (loading) {
      <p class="text-sm">Loading…</p>
    } @else {
      <p class="text-sm text-red-700">Not found.</p>
    }
  `,
})
export class QADetailComponent implements OnInit {
  private readonly qaService = inject(QAService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  entry: QAEntry | null = null;
  loading = false;

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loading = true;
      this.qaService.get(id).subscribe({
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
  }

  remove(): void {
    if (!this.entry || !confirm('Delete this Q&A entry?')) return;
    this.qaService.delete(this.entry.id).subscribe({
      next: () => this.router.navigate(['/qa']),
    });
  }
}
