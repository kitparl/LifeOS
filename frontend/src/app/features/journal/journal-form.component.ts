import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { JOURNAL_TYPES, JournalType } from './models/journal.models';
import { JournalService } from './services/journal.service';

@Component({
  selector: 'app-journal-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  template: `
    <div class="max-w-lg">
      <div class="panel !p-0 overflow-hidden">
        <div class="title-bar rounded-none border-x-0 border-t-0">{{ isEdit ? 'Edit Entry' : 'New Entry' }}</div>
        <form class="space-y-3 p-4 text-sm" [formGroup]="form" (ngSubmit)="submit()">
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="mb-1 block">Date</label>
              <input class="input-field" type="date" formControlName="entry_date" />
            </div>
            <div>
              <label class="mb-1 block">Type</label>
              <select class="input-field" formControlName="entry_type">
                @for (t of types; track t.value) {
                  <option [value]="t.value">{{ t.label }}</option>
                }
              </select>
            </div>
          </div>
          <div>
            <label class="mb-1 block">Title (optional)</label>
            <input class="input-field" formControlName="title" />
          </div>
          <div>
            <label class="mb-1 block">Content</label>
            <textarea class="input-field min-h-[100px]" formControlName="content"></textarea>
          </div>
          <div>
            <label class="mb-1 block">Gratitude</label>
            <textarea class="input-field min-h-[60px]" formControlName="gratitude"></textarea>
          </div>
          <div>
            <label class="mb-1 block">Wins</label>
            <textarea class="input-field min-h-[60px]" formControlName="wins"></textarea>
          </div>
          <div>
            <label class="mb-1 block">Lessons</label>
            <textarea class="input-field min-h-[60px]" formControlName="lessons"></textarea>
          </div>
          @if (error) {
            <p class="text-xs text-red-700">{{ error }}</p>
          }
          <div class="flex gap-2">
            <button type="submit" class="btn-primary" [disabled]="form.invalid || saving">
              {{ saving ? 'Saving…' : 'Save' }}
            </button>
            <a routerLink="/journal" class="input-field !w-auto inline-flex items-center no-underline text-gray-700">Cancel</a>
          </div>
        </form>
      </div>
    </div>
  `,
})
export class JournalFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly journalService = inject(JournalService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  types = JOURNAL_TYPES;
  isEdit = false;
  entryId: string | null = null;
  saving = false;
  error = '';

  form = this.fb.nonNullable.group({
    entry_date: [new Date().toISOString().slice(0, 10), Validators.required],
    entry_type: ['morning' as JournalType, Validators.required],
    title: [''],
    content: ['', Validators.required],
    gratitude: [''],
    wins: [''],
    lessons: [''],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    const url = this.route.snapshot.url.map((s) => s.path).join('/');
    if (id && url.endsWith('edit')) {
      this.isEdit = true;
      this.entryId = id;
      this.journalService.get(id).subscribe({
        next: (entry) => {
          this.form.patchValue({
            entry_date: entry.entry_date.slice(0, 10),
            entry_type: entry.entry_type,
            title: entry.title ?? '',
            content: entry.content,
            gratitude: entry.gratitude ?? '',
            wins: entry.wins ?? '',
            lessons: entry.lessons ?? '',
          });
        },
      });
    }
  }

  submit(): void {
    if (this.form.invalid) return;
    this.saving = true;
    this.error = '';
    const raw = this.form.getRawValue();
    const payload = {
      entry_date: raw.entry_date,
      entry_type: raw.entry_type,
      title: raw.title || null,
      content: raw.content,
      gratitude: raw.gratitude || null,
      wins: raw.wins || null,
      lessons: raw.lessons || null,
    };

    const req =
      this.isEdit && this.entryId
        ? this.journalService.update(this.entryId, payload)
        : this.journalService.create(payload);

    req.subscribe({
      next: (entry) => this.router.navigate(['/journal', entry.id]),
      error: (err) => {
        this.error = typeof err?.error?.detail === 'string' ? err.error.detail : 'Failed to save entry';
        this.saving = false;
      },
    });
  }
}
