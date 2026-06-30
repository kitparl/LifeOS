import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { VocabularyWord } from './models/communication.models';
import { CommunicationService } from './services/communication.service';

@Component({
  selector: 'app-vocabulary-detail',
  standalone: true,
  imports: [RouterLink],
  template: `
    @if (word; as w) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <h1 class="text-lg font-semibold">{{ w.word }}</h1>
          <div class="flex gap-2">
            <a [routerLink]="['/communication/vocabulary', w.id, 'edit']" class="btn-primary text-xs no-underline">Edit</a>
            <button type="button" class="input-field !w-auto text-xs text-red-700" (click)="remove()">Delete</button>
          </div>
        </div>
        <div class="panel text-sm space-y-2">
          <p><span class="font-medium">Meaning:</span> {{ w.meaning }}</p>
          @if (w.pronunciation) {
            <p><span class="font-medium">Pronunciation:</span> {{ w.pronunciation }}</p>
          }
          @if (w.synonyms) {
            <p><span class="font-medium">Synonyms:</span> {{ w.synonyms }}</p>
          }
          <p><span class="font-medium">Mastery:</span> {{ w.mastery }}/5</p>
          @if (w.examples) {
            <p class="whitespace-pre-wrap"><span class="font-medium">Examples:</span> {{ w.examples }}</p>
          }
          @if (w.notes) {
            <p class="whitespace-pre-wrap"><span class="font-medium">Notes:</span> {{ w.notes }}</p>
          }
        </div>
        <a routerLink="/communication" class="text-sm text-[var(--xp-blue)] underline">Back</a>
      </div>
    } @else if (loading) {
      <p class="text-sm">Loading…</p>
    } @else {
      <p class="text-sm text-red-700">Not found.</p>
    }
  `,
})
export class VocabularyDetailComponent implements OnInit {
  private readonly communication = inject(CommunicationService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  word: VocabularyWord | null = null;
  loading = false;

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loading = true;
      this.communication.getVocabulary(id).subscribe({
        next: (w) => {
          this.word = w;
          this.loading = false;
        },
        error: () => {
          this.word = null;
          this.loading = false;
        },
      });
    }
  }

  remove(): void {
    if (!this.word || !confirm('Delete this word?')) return;
    this.communication.deleteVocabulary(this.word.id).subscribe({
      next: () => this.router.navigate(['/communication']),
    });
  }
}
