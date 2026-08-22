import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ModalComponent } from '../../shared/modal/modal.component';
import {
  KnowledgeSearchHit,
  KnowledgeSubjectListItem,
} from './models/knowledge-notes.models';
import { KnowledgeNotesService } from './services/knowledge-notes.service';

@Component({
  selector: 'app-knowledge-notes-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, ModalComponent],
  template: `
    <div class="space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-lg font-semibold">Knowledge Notes</h1>
        <button type="button" class="btn-primary text-xs" (click)="openCreate()">New Subject</button>
      </div>

      <form class="flex flex-wrap gap-2 text-sm" (ngSubmit)="runSearch()">
        <input
          class="input-field !w-64 max-w-full"
          [formControl]="searchControl"
          placeholder="Search across all notes…"
        />
        <button type="submit" class="btn-secondary text-xs">Search</button>
        @if (hits() !== null) {
          <button type="button" class="btn-ghost text-xs" (click)="clearSearch()">Clear</button>
        }
      </form>

      @if (hits(); as results) {
        @if (results.length === 0) {
          <p class="text-sm" style="color: var(--text-muted)">No matches found.</p>
        } @else {
          <ul class="panel !p-0 divide-y" style="border-color: var(--border)">
            @for (h of results; track h.section_id) {
              <li class="px-3 py-2">
                <a
                  class="link text-sm font-medium"
                  [routerLink]="['/knowledge', h.subject_id]"
                  [queryParams]="{ section: h.section_id }"
                >{{ h.section_title }}</a>
                <p class="text-xs" style="color: var(--text-muted)">
                  {{ h.subject_title }} › {{ h.chapter_title }}
                </p>
                @if (h.snippet) {
                  <p class="mt-1 text-xs" style="color: var(--text-muted)">{{ h.snippet }}</p>
                }
              </li>
            }
          </ul>
        }
      }

      @if (loading()) {
        <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
      } @else if (subjects().length === 0) {
        <div class="empty-state">
          <div class="empty-state__icon">📚</div>
          <p class="empty-state__title">No subjects yet</p>
          <p class="empty-state__desc">Create a subject to start organizing your knowledge into chapters and sections.</p>
          <button type="button" class="btn-primary mt-2 text-xs" (click)="openCreate()">New Subject</button>
        </div>
      } @else {
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          @for (s of subjects(); track s.id) {
            <div class="panel relative" style="color: var(--text)">
              <button
                type="button"
                class="btn-ghost kn-card-edit"
                aria-label="Edit subject"
                title="Edit subject"
                (click)="openEdit(s, $event)"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M12 20h9"></path>
                  <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                </svg>
              </button>
              <a
                [routerLink]="['/knowledge', s.id]"
                class="block no-underline pr-7 transition hover:opacity-90"
                style="color: inherit"
              >
                <div class="flex items-start gap-2">
                  <span class="text-2xl leading-none">{{ s.icon || '📘' }}</span>
                  <div class="min-w-0 flex-1">
                    <p class="truncate font-semibold">{{ s.title }}</p>
                    <p
                      class="mt-0.5 line-clamp-2 text-xs"
                      style="color: var(--text-muted)"
                      [class.italic]="!s.description"
                    >{{ s.description || 'Add description…' }}</p>
                    <p class="mt-2 text-xs" style="color: var(--text-faint)">
                      {{ s.chapter_count }} chapters · {{ s.section_count }} sections
                    </p>
                  </div>
                </div>
              </a>
            </div>
          }
        </div>
      }
    </div>

    <app-modal
      [open]="formOpen()"
      [title]="formMode() === 'edit' ? 'Edit Subject' : 'New Subject'"
      (closed)="closeForm()"
    >
      <form [formGroup]="subjectForm" (ngSubmit)="submitForm()" class="space-y-3 text-sm" body>
        <div>
          <label class="mb-1 block">Title</label>
          <input class="input-field" formControlName="title" placeholder="e.g. System Design" />
        </div>
        <div>
          <label class="mb-1 block">Icon (emoji, optional)</label>
          <input class="input-field" formControlName="icon" placeholder="📘" maxlength="4" />
        </div>
        <div>
          <label class="mb-1 block">Description (optional)</label>
          <textarea class="input-field min-h-[70px]" formControlName="description"></textarea>
        </div>
      </form>
      <div footer class="flex justify-end gap-3">
        <button type="button" class="btn-secondary text-xs" (click)="closeForm()">Cancel</button>
        <button type="button" class="btn-primary text-xs" [disabled]="subjectForm.invalid || saving()" (click)="submitForm()">
          {{ saving() ? (formMode() === 'edit' ? 'Saving…' : 'Creating…') : (formMode() === 'edit' ? 'Save' : 'Create') }}
        </button>
      </div>
    </app-modal>
  `,
  styles: [
    `
      .kn-card-edit {
        position: absolute;
        top: 0.5rem;
        right: 0.5rem;
        z-index: 1;
        width: 28px;
        height: 28px;
        min-width: 28px;
        padding: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
      }
    `,
  ],
})
export class KnowledgeNotesListComponent implements OnInit {
  private readonly service = inject(KnowledgeNotesService);
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);

  readonly subjects = signal<KnowledgeSubjectListItem[]>([]);
  readonly hits = signal<KnowledgeSearchHit[] | null>(null);
  readonly loading = signal(false);
  readonly formOpen = signal(false);
  readonly formMode = signal<'create' | 'edit'>('create');
  readonly saving = signal(false);

  private editingId: string | null = null;

  readonly searchControl = this.fb.nonNullable.control('');
  subjectForm = this.fb.nonNullable.group({
    title: ['', Validators.required],
    icon: [''],
    description: [''],
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.service.listSubjects().subscribe({
      next: (s) => {
        this.subjects.set(s);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  runSearch(): void {
    const q = this.searchControl.value.trim();
    if (!q) {
      this.hits.set(null);
      return;
    }
    this.service.search(q).subscribe({ next: (h) => this.hits.set(h) });
  }

  clearSearch(): void {
    this.searchControl.setValue('');
    this.hits.set(null);
  }

  openCreate(): void {
    this.formMode.set('create');
    this.editingId = null;
    this.subjectForm.reset({ title: '', icon: '', description: '' });
    this.formOpen.set(true);
  }

  openEdit(subject: KnowledgeSubjectListItem, event: Event): void {
    event.preventDefault();
    event.stopPropagation();
    this.formMode.set('edit');
    this.editingId = subject.id;
    this.subjectForm.reset({
      title: subject.title,
      icon: subject.icon ?? '',
      description: subject.description ?? '',
    });
    this.formOpen.set(true);
  }

  closeForm(): void {
    this.formOpen.set(false);
    this.editingId = null;
  }

  submitForm(): void {
    if (this.subjectForm.invalid || this.saving()) return;
    this.saving.set(true);
    const raw = this.subjectForm.getRawValue();
    const payload = {
      title: raw.title,
      icon: raw.icon || null,
      description: raw.description || null,
    };

    if (this.formMode() === 'edit' && this.editingId) {
      this.service.updateSubject(this.editingId, payload).subscribe({
        next: () => {
          this.subjects.update((list) =>
            list.map((s) => (s.id === this.editingId ? { ...s, ...payload } : s))
          );
          this.saving.set(false);
          this.closeForm();
        },
        error: () => this.saving.set(false),
      });
      return;
    }

    this.service.createSubject(payload).subscribe({
      next: (subject) => {
        this.saving.set(false);
        this.closeForm();
        this.router.navigate(['/knowledge', subject.id]);
      },
      error: () => this.saving.set(false),
    });
  }
}
