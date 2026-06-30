import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { QAService } from './services/qa.service';

@Component({
  selector: 'app-qa-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="max-w-lg">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">{{ isEdit ? 'Edit Q&A' : 'New Q&A' }}</div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div>
            <label class="mb-1 block">Question</label>
            <textarea class="input-field min-h-[60px]" formControlName="question"></textarea>
          </div>
          <div>
            <label class="mb-1 block">Answer</label>
            <textarea class="input-field min-h-[120px]" formControlName="answer"></textarea>
          </div>
          <div>
            <label class="mb-1 block">Tags (comma-separated)</label>
            <input class="input-field" formControlName="tags" />
          </div>
          @if (error) {
            <p class="text-xs text-red-700">{{ error }}</p>
          }
          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">{{ saving ? 'Saving…' : 'Save' }}</button>
            <a routerLink="/qa" class="input-field !w-auto inline-flex items-center no-underline text-gray-700">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  `,
})
export class QAFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly qaService = inject(QAService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  isEdit = false;
  entryId: string | null = null;
  saving = false;
  error = '';

  form = this.fb.nonNullable.group({
    question: ['', Validators.required],
    answer: ['', Validators.required],
    tags: [''],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.entryId = id;
      this.qaService.get(id).subscribe({
        next: (e) =>
          this.form.patchValue({
            question: e.question,
            answer: e.current_answer,
            tags: e.tags.join(', '),
          }),
      });
    }
  }

  submit(): void {
    if (this.form.invalid) return;
    this.saving = true;
    const raw = this.form.getRawValue();
    const tags = raw.tags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);
    const payload = { question: raw.question, answer: raw.answer, tags };
    const req =
      this.isEdit && this.entryId
        ? this.qaService.update(this.entryId, payload)
        : this.qaService.create(payload);
    req.subscribe({
      next: (e) => this.router.navigate(['/qa', e.id]),
      error: (err) => {
        this.error = err?.error?.detail || 'Failed to save';
        this.saving = false;
      },
    });
  }
}
