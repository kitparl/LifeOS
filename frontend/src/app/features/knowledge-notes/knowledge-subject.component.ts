import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MarkdownEditorComponent } from '../../shared/markdown-editor/markdown-editor.component';
import { MarkdownPipe } from '../../shared/markdown/markdown.pipe';
import { ModalComponent } from '../../shared/modal/modal.component';
import {
  KnowledgeChapter,
  KnowledgeSection,
  KnowledgeSubjectDetail,
} from './models/knowledge-notes.models';
import { KnowledgeNotesService } from './services/knowledge-notes.service';

type PromptAction =
  | 'add-chapter'
  | 'rename-chapter'
  | 'add-section'
  | 'rename-section'
  | 'rename-subject';

@Component({
  selector: 'app-knowledge-subject',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, MarkdownEditorComponent, MarkdownPipe, ModalComponent],
  template: `
    @if (subject(); as s) {
      <div class="space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div class="flex items-center gap-2 min-w-0">
            <a routerLink="/knowledge" class="btn-ghost text-xs no-underline">← Notes</a>
            <h1 class="truncate text-lg font-semibold">{{ s.icon || '📘' }} {{ s.title }}</h1>
          </div>
          <div class="flex gap-2">
            <button type="button" class="btn-secondary text-xs" (click)="prompt('rename-subject', s.title)">Rename</button>
            <button type="button" class="btn-danger text-xs" (click)="deleteSubject()">Delete</button>
          </div>
        </div>

        <div class="kn-layout">
          <!-- Chapter / section navigation -->
          <aside class="kn-sidebar">
            <div class="flex items-center justify-between px-1 pb-1">
              <span class="section-heading">Chapters</span>
              <button type="button" class="btn-ghost !px-2 text-xs" (click)="prompt('add-chapter')">+ Add</button>
            </div>
            @if (s.chapters.length === 0) {
              <p class="px-1 text-xs" style="color: var(--text-muted)">No chapters yet.</p>
            }
            @for (c of s.chapters; track c.id) {
              <div class="kn-chapter">
                <div class="kn-chapter__head">
                  <span class="truncate font-medium text-sm">{{ c.title }}</span>
                  <span class="kn-chapter__actions">
                    <button type="button" title="Add section" (click)="promptSection(c)">＋</button>
                    <button type="button" title="Rename" (click)="promptRenameChapter(c)">✎</button>
                    <button type="button" title="Delete" (click)="deleteChapter(c)">🗑</button>
                  </span>
                </div>
                @for (sec of c.sections; track sec.id) {
                  <button
                    type="button"
                    class="kn-section-link"
                    [class.active]="selected()?.id === sec.id"
                    (click)="selectSection(sec)"
                  >{{ sec.title }}</button>
                }
              </div>
            }
          </aside>

          <!-- Section editor / viewer -->
          <section class="kn-main">
            @if (selected(); as sec) {
              <form [formGroup]="form" class="space-y-2">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <input class="kn-section-title" formControlName="title" placeholder="Section title" />
                  <div class="flex items-center gap-2">
                    <button type="button" class="btn-ghost text-xs" (click)="togglePreview()">
                      {{ previewOnly() ? 'Edit' : 'Read' }}
                    </button>
                    <button type="button" class="btn-danger text-xs" (click)="deleteSection(sec)">Delete</button>
                    <button type="button" class="btn-primary text-xs" [disabled]="saving()" (click)="save()">
                      {{ saving() ? 'Saving…' : 'Save' }}
                    </button>
                  </div>
                </div>
                @if (previewOnly()) {
                  <div class="markdown-body panel" [innerHTML]="form.controls.content.value | markdown"></div>
                } @else {
                  <app-markdown-editor formControlName="content" minHeight="52vh" placeholder="Write this section in Markdown…" />
                }
              </form>
            } @else {
              <div class="empty-state">
                <div class="empty-state__icon">📝</div>
                <p class="empty-state__title">Select a section</p>
                <p class="empty-state__desc">Choose a section on the left, or add a chapter and section to begin writing.</p>
              </div>
            }
          </section>
        </div>
      </div>
    } @else if (loading()) {
      <p class="text-sm">Loading…</p>
    } @else {
      <p class="text-sm" style="color: var(--danger)">Subject not found.</p>
    }

    <app-modal [open]="promptOpen()" [title]="promptTitle()" (closed)="promptOpen.set(false)">
      <div body>
        <input
          class="input-field"
          [formControl]="promptControl"
          (keydown.enter)="confirmPrompt()"
          placeholder="Name"
        />
      </div>
      <div footer>
        <button type="button" class="btn-secondary text-xs" (click)="promptOpen.set(false)">Cancel</button>
        <button type="button" class="btn-primary text-xs" [disabled]="!promptControl.value.trim()" (click)="confirmPrompt()">Save</button>
      </div>
    </app-modal>
  `,
})
export class KnowledgeSubjectComponent implements OnInit {
  private readonly service = inject(KnowledgeNotesService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);

  readonly subject = signal<KnowledgeSubjectDetail | null>(null);
  readonly selected = signal<KnowledgeSection | null>(null);
  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly previewOnly = signal(false);

  readonly promptOpen = signal(false);
  readonly promptTitle = signal('');
  readonly promptControl = this.fb.nonNullable.control('');
  private promptAction: PromptAction = 'add-chapter';
  private promptTargetId: string | null = null;

  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    content: [''],
  });

  private pendingSectionId: string | null = null;

  ngOnInit(): void {
    this.pendingSectionId = this.route.snapshot.queryParamMap.get('section');
    const id = this.route.snapshot.paramMap.get('id');
    if (id) this.load(id);
  }

  private load(id: string): void {
    this.loading.set(true);
    this.service.getSubject(id).subscribe({
      next: (s) => {
        this.subject.set(s);
        this.loading.set(false);
        this.restoreSelection();
      },
      error: () => this.loading.set(false),
    });
  }

  private restoreSelection(): void {
    const s = this.subject();
    if (!s) return;
    const all = s.chapters.flatMap((c) => c.sections);
    const target =
      (this.pendingSectionId && all.find((sec) => sec.id === this.pendingSectionId)) ||
      (this.selected() && all.find((sec) => sec.id === this.selected()!.id)) ||
      all[0] ||
      null;
    this.pendingSectionId = null;
    if (target) this.selectSection(target);
    else this.selected.set(null);
  }

  selectSection(sec: KnowledgeSection): void {
    this.selected.set(sec);
    this.previewOnly.set(false);
    this.form.reset({ title: sec.title, content: sec.content });
  }

  togglePreview(): void {
    this.previewOnly.set(!this.previewOnly());
  }

  save(): void {
    const sec = this.selected();
    if (!sec || this.form.invalid) return;
    this.saving.set(true);
    const raw = this.form.getRawValue();
    this.service.updateSection(sec.id, { title: raw.title, content: raw.content }).subscribe({
      next: (updated) => {
        this.saving.set(false);
        this.patchSection(updated);
      },
      error: () => this.saving.set(false),
    });
  }

  private patchSection(updated: KnowledgeSection): void {
    const s = this.subject();
    if (!s) return;
    for (const c of s.chapters) {
      const idx = c.sections.findIndex((x) => x.id === updated.id);
      if (idx !== -1) c.sections[idx] = updated;
    }
    this.subject.set({ ...s });
    this.selected.set(updated);
  }

  deleteSection(sec: KnowledgeSection): void {
    if (!confirm(`Delete section "${sec.title}"?`)) return;
    this.service.deleteSection(sec.id).subscribe({ next: () => this.reload() });
  }

  deleteChapter(c: KnowledgeChapter): void {
    if (!confirm(`Delete chapter "${c.title}" and all its sections?`)) return;
    this.service.deleteChapter(c.id).subscribe({ next: () => this.reload() });
  }

  deleteSubject(): void {
    const s = this.subject();
    if (!s || !confirm(`Delete subject "${s.title}" and everything in it?`)) return;
    this.service.deleteSubject(s.id).subscribe({ next: () => this.router.navigate(['/knowledge']) });
  }

  // ---- Prompt modal ----
  prompt(action: PromptAction, value = ''): void {
    this.promptAction = action;
    this.promptTargetId = null;
    this.promptTitle.set(this.titleFor(action));
    this.promptControl.setValue(value);
    this.promptOpen.set(true);
  }

  promptSection(c: KnowledgeChapter): void {
    this.promptAction = 'add-section';
    this.promptTargetId = c.id;
    this.promptTitle.set('New Section');
    this.promptControl.setValue('');
    this.promptOpen.set(true);
  }

  promptRenameChapter(c: KnowledgeChapter): void {
    this.promptAction = 'rename-chapter';
    this.promptTargetId = c.id;
    this.promptTitle.set('Rename Chapter');
    this.promptControl.setValue(c.title);
    this.promptOpen.set(true);
  }

  private titleFor(action: PromptAction): string {
    switch (action) {
      case 'add-chapter': return 'New Chapter';
      case 'rename-subject': return 'Rename Subject';
      default: return 'Name';
    }
  }

  confirmPrompt(): void {
    const value = this.promptControl.value.trim();
    if (!value) return;
    const s = this.subject();
    if (!s) return;
    const done = () => {
      this.promptOpen.set(false);
      this.reload();
    };
    switch (this.promptAction) {
      case 'add-chapter':
        this.service.createChapter(s.id, { title: value }).subscribe({ next: done });
        break;
      case 'rename-chapter':
        if (this.promptTargetId)
          this.service.updateChapter(this.promptTargetId, { title: value }).subscribe({ next: done });
        break;
      case 'add-section':
        if (this.promptTargetId)
          this.service.createSection(this.promptTargetId, { title: value, content: '' }).subscribe({
            next: (sec) => {
              this.promptOpen.set(false);
              this.pendingSectionId = sec.id;
              this.reload();
            },
          });
        break;
      case 'rename-subject':
        this.service.updateSubject(s.id, { title: value }).subscribe({ next: done });
        break;
    }
  }

  private reload(): void {
    const s = this.subject();
    if (s) this.load(s.id);
  }
}
