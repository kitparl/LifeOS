import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { WritingPractice } from './models/communication.models';
import { CommunicationService } from './services/communication.service';

@Component({
  selector: 'app-writing-detail',
  standalone: true,
  imports: [RouterLink],
  template: `
    @if (item; as w) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 class="text-lg font-semibold">{{ w.title }}</h1>
            <p class="text-xs capitalize text-gray-600">{{ w.category.replace('_', ' ') }}</p>
          </div>
          <div class="flex gap-2">
            <a [routerLink]="['/communication/writing', w.id, 'edit']" class="btn-primary text-xs no-underline">Edit</a>
            <button type="button" class="input-field !w-auto text-xs text-red-700" (click)="remove()">Delete</button>
          </div>
        </div>
        <div class="panel text-sm whitespace-pre-wrap text-gray-700">{{ w.content || 'No content' }}</div>
        <a routerLink="/communication" class="text-sm text-[var(--xp-blue)] underline">Back</a>
      </div>
    } @else if (loading) {
      <p class="text-sm">Loading…</p>
    } @else {
      <p class="text-sm text-red-700">Not found.</p>
    }
  `,
})
export class WritingDetailComponent implements OnInit {
  private readonly communication = inject(CommunicationService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  item: WritingPractice | null = null;
  loading = false;

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loading = true;
      this.communication.getWriting(id).subscribe({
        next: (w) => {
          this.item = w;
          this.loading = false;
        },
        error: () => {
          this.item = null;
          this.loading = false;
        },
      });
    }
  }

  remove(): void {
    if (!this.item || !confirm('Delete this writing?')) return;
    this.communication.deleteWriting(this.item.id).subscribe({
      next: () => this.router.navigate(['/communication']),
    });
  }
}
