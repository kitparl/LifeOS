import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MarkdownEditorComponent } from '../../shared/markdown-editor/markdown-editor.component';
import { JOURNAL_TYPES, JournalType } from './models/journal.models';
import { JournalService } from './services/journal.service';

@Component({
  selector: 'app-journal-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, MarkdownEditorComponent],
  template: `
    <form class="journal-writer" [formGroup]="form" (ngSubmit)="submit()">
      <div class="journal-writer__bar">
        <a routerLink="/journal" class="btn-ghost text-xs no-underline">← Journal</a>
        <div class="flex items-center gap-2">
          @if (error) {
            <span class="text-xs" style="color: var(--danger)">{{ error }}</span>
          }
          <a routerLink="/journal" class="btn-secondary text-xs no-underline">Cancel</a>
          <button type="submit" class="btn-primary text-xs" [disabled]="form.invalid || saving">
            {{ saving ? 'Saving…' : 'Save entry' }}
          </button>
        </div>
      </div>

      <input
        class="journal-writer__title"
        formControlName="title"
        placeholder="Untitled entry"
        aria-label="Title"
      />

      <div class="journal-writer__meta">
        <input class="journal-writer__date" type="date" formControlName="entry_date" aria-label="Date" />
        <select class="journal-writer__date" formControlName="entry_type" aria-label="Type">
          @for (t of types; track t.value) {
            <option [value]="t.value">{{ t.label }}</option>
          }
        </select>
      </div>

      <app-markdown-editor
        formControlName="content"
        placeholder="Write freely… what happened today, how you felt, what's on your mind."
        minHeight="46vh"
      />

      <div class="journal-section">
        <label class="journal-section__label">Gratitude</label>
        <textarea
          class="journal-textarea"
          formControlName="gratitude"
          placeholder="What are you grateful for today?"
        ></textarea>
      </div>

      <div class="journal-section">
        <label class="journal-section__label">Wins</label>
        <textarea
          class="journal-textarea"
          formControlName="wins"
          placeholder="What went well? Small wins count."
        ></textarea>
      </div>

      <div class="journal-section">
        <label class="journal-section__label">Lessons Learned</label>
        <textarea
          class="journal-textarea"
          formControlName="lessons"
          placeholder="What did you learn or would do differently?"
        ></textarea>
      </div>
    </form>
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
