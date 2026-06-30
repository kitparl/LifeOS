import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { SpeakingPractice } from './models/communication.models';
import { CommunicationService } from './services/communication.service';

@Component({
  selector: 'app-speaking-detail',
  standalone: true,
  imports: [RouterLink],
  template: `
    @if (item; as s) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 class="text-lg font-semibold">{{ s.title }}</h1>
            <p class="text-xs capitalize text-gray-600">{{ s.category.replace('_', ' ') }}</p>
          </div>
          <div class="flex gap-2">
            <a [routerLink]="['/communication/speaking', s.id, 'edit']" class="btn-primary text-xs no-underline">Edit</a>
            <button type="button" class="input-field !w-auto text-xs text-red-700" (click)="remove()">Delete</button>
          </div>
        </div>
        <div class="panel text-sm">
          <p class="font-medium mb-1">Prompt</p>
          <p class="whitespace-pre-wrap text-gray-700">{{ s.prompt }}</p>
        </div>
        @if (s.response) {
          <div class="panel text-sm">
            <p class="font-medium mb-1">Response</p>
            <p class="whitespace-pre-wrap text-gray-700">{{ s.response }}</p>
          </div>
        }
        @if (s.notes) {
          <div class="panel text-sm">
            <p class="font-medium mb-1">Notes</p>
            <p class="whitespace-pre-wrap text-gray-700">{{ s.notes }}</p>
          </div>
        }
        <a routerLink="/communication" class="text-sm text-[var(--xp-blue)] underline">Back</a>
      </div>
    } @else if (loading) {
      <p class="text-sm">Loading…</p>
    } @else {
      <p class="text-sm text-red-700">Not found.</p>
    }
  `,
})
export class SpeakingDetailComponent implements OnInit {
  private readonly communication = inject(CommunicationService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  item: SpeakingPractice | null = null;
  loading = false;

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loading = true;
      this.communication.getSpeaking(id).subscribe({
        next: (s) => {
          this.item = s;
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
    if (!this.item || !confirm('Delete this practice?')) return;
    this.communication.deleteSpeaking(this.item.id).subscribe({
      next: () => this.router.navigate(['/communication']),
    });
  }
}
