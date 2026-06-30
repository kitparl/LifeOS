import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { WRITING_CATEGORIES, WritingCategory } from './models/communication.models';
import { CommunicationService } from './services/communication.service';

@Component({
  selector: 'app-writing-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="max-w-lg">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">{{ isEdit ? 'Edit Writing' : 'New Writing' }}</div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div>
            <label class="mb-1 block">Title</label>
            <input class="input-field" formControlName="title" />
          </div>
          <div>
            <label class="mb-1 block">Category</label>
            <select class="input-field" formControlName="category">
              @for (c of categories; track c.value) {
                <option [value]="c.value">{{ c.label }}</option>
              }
            </select>
          </div>
          <div>
            <label class="mb-1 block">Content</label>
            <textarea class="input-field min-h-[160px]" formControlName="content"></textarea>
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
export class WritingFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly communication = inject(CommunicationService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  categories = WRITING_CATEGORIES;
  isEdit = false;
  itemId: string | null = null;
  saving = false;
  error = '';

  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    category: ['notes' as WritingCategory, Validators.required],
    content: [''],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.itemId = id;
      this.communication.getWriting(id).subscribe({
        next: (w) => this.form.patchValue({ title: w.title, category: w.category, content: w.content }),
      });
    }
  }

  submit(): void {
    if (this.form.invalid) return;
    this.saving = true;
    const raw = this.form.getRawValue();
    const req =
      this.isEdit && this.itemId
        ? this.communication.updateWriting(this.itemId, raw)
        : this.communication.createWriting(raw);
    req.subscribe({
      next: (w) => this.router.navigate(['/communication/writing', w.id]),
      error: (err) => {
        this.error = err?.error?.detail || 'Failed to save';
        this.saving = false;
      },
    });
  }
}
