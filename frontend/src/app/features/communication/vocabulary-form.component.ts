import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommunicationService } from './services/communication.service';

@Component({
  selector: 'app-vocabulary-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="max-w-lg">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">{{ isEdit ? 'Edit Word' : 'Add Word' }}</div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div>
            <label class="mb-1 block">Word</label>
            <input class="input-field" formControlName="word" />
          </div>
          <div>
            <label class="mb-1 block">Meaning</label>
            <textarea class="input-field min-h-[60px]" formControlName="meaning"></textarea>
          </div>
          <div>
            <label class="mb-1 block">Examples</label>
            <textarea class="input-field min-h-[60px]" formControlName="examples"></textarea>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="mb-1 block">Pronunciation</label>
              <input class="input-field" formControlName="pronunciation" />
            </div>
            <div>
              <label class="mb-1 block">Mastery (1–5)</label>
              <input class="input-field" type="number" min="1" max="5" formControlName="mastery" />
            </div>
          </div>
          <div>
            <label class="mb-1 block">Synonyms</label>
            <input class="input-field" formControlName="synonyms" />
          </div>
          <div>
            <label class="mb-1 block">Notes</label>
            <textarea class="input-field min-h-[50px]" formControlName="notes"></textarea>
          </div>
          @if (error) {
            <p class="text-xs text-red-700">{{ error }}</p>
          }
          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">{{ saving ? 'Saving…' : 'Save' }}</button>
            <a routerLink="/communication" class="input-field !w-auto inline-flex items-center no-underline text-gray-700">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  `,
})
export class VocabularyFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly communication = inject(CommunicationService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  isEdit = false;
  wordId: string | null = null;
  saving = false;
  error = '';

  form = this.fb.nonNullable.group({
    word: ['', Validators.required],
    meaning: ['', Validators.required],
    examples: [''],
    pronunciation: [''],
    synonyms: [''],
    mastery: [1, [Validators.min(1), Validators.max(5)]],
    notes: [''],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.wordId = id;
      this.communication.getVocabulary(id).subscribe({
        next: (w) =>
          this.form.patchValue({
            word: w.word,
            meaning: w.meaning,
            examples: w.examples ?? '',
            pronunciation: w.pronunciation ?? '',
            synonyms: w.synonyms ?? '',
            mastery: w.mastery,
            notes: w.notes ?? '',
          }),
      });
    }
  }

  submit(): void {
    if (this.form.invalid) return;
    this.saving = true;
    const raw = this.form.getRawValue();
    const payload = {
      word: raw.word,
      meaning: raw.meaning,
      examples: raw.examples || null,
      pronunciation: raw.pronunciation || null,
      synonyms: raw.synonyms || null,
      mastery: raw.mastery,
      notes: raw.notes || null,
    };
    const req =
      this.isEdit && this.wordId
        ? this.communication.updateVocabulary(this.wordId, payload)
        : this.communication.createVocabulary(payload);
    req.subscribe({
      next: (w) => this.router.navigate(['/communication/vocabulary', w.id]),
      error: (err) => {
        this.error = err?.error?.detail || 'Failed to save';
        this.saving = false;
      },
    });
  }
}
