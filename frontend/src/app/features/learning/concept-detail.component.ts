import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { KnowledgeSubjectListItem } from '../knowledge-notes/models/knowledge-notes.models';
import { KnowledgeNotesService } from '../knowledge-notes/services/knowledge-notes.service';
import {
  ConceptNote,
  LearningConcept,
  LearningResource,
  StudySession,
} from './models/learning.models';
import { LearningService } from './services/learning.service';

@Component({
  selector: 'app-learning-concept-detail',
  standalone: true,
  imports: [RouterLink, ReactiveFormsModule],
  template: `
    <div class="space-y-3 max-w-2xl">
      <a routerLink="/learning/tracks" class="link text-sm">← Tracks</a>
      @if (loading()) {
        <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
      } @else if (concept()) {
        <div class="panel space-y-2">
          <h1 class="text-lg font-semibold">{{ concept()!.title }}</h1>
          @if (concept()!.summary) {
            <p class="text-sm" style="color: var(--text-muted)">{{ concept()!.summary }}</p>
          }
          <p class="text-xs" style="color: var(--text-muted)">
            @if (concept()!.week_number) {
              Week {{ concept()!.week_number }} ·
            }
            {{ concept()!.estimated_minutes ?? '—' }} min estimated
          </p>
        </div>

        <div class="panel space-y-2">
          <h2 class="text-sm font-semibold">Depth gate</h2>
          <form class="space-y-2 text-sm" [formGroup]="gateForm" (ngSubmit)="saveGate()">
            <label class="flex items-center gap-2">
              <input type="checkbox" formControlName="can_explain" />
              Can explain without notes
            </label>
            <label class="flex items-center gap-2">
              <input type="checkbox" formControlName="failure_modes_known" />
              Know at least two failure modes
            </label>
            <label class="flex items-center gap-2">
              <input type="checkbox" formControlName="tradeoffs_known" />
              Can state the trade-off vs alternative
            </label>
            <label class="block">
              <span class="text-xs" style="color: var(--text-muted)">Confidence (0–5)</span>
              <input class="input-field" type="number" min="0" max="5" formControlName="confidence" />
            </label>
            <label class="block">
              <span class="text-xs" style="color: var(--text-muted)">Artifact URL</span>
              <input class="input-field" formControlName="artifact_url" placeholder="https://…" />
            </label>
            <button type="submit" class="btn-primary text-xs" [disabled]="saving()">Save</button>
          </form>
        </div>

        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Resources</div>
          @if (resources().length === 0) {
            <p class="p-3 text-sm" style="color: var(--text-muted)">No resources linked.</p>
          } @else {
            <ul class="divide-y divide-[var(--xp-border)] text-sm">
              @for (r of resources(); track r.id) {
                <li class="flex items-center justify-between gap-2 px-3 py-2">
                  <div>
                    <a [href]="r.url" target="_blank" rel="noopener" class="link">{{ r.title }}</a>
                    <p class="text-xs" style="color: var(--text-muted)">
                      {{ r.resource_type }} · {{ r.priority }}
                      @if (r.author) {
                        · {{ r.author }}
                      }
                    </p>
                  </div>
                  <button
                    type="button"
                    class="input-field !w-auto text-xs"
                    (click)="toggleConsumed(r)"
                  >
                    {{ r.is_consumed ? 'Consumed' : 'Mark done' }}
                  </button>
                </li>
              }
            </ul>
          }
        </div>

        @if (inheritedResources().length > 0) {
          <div class="panel !p-0 overflow-hidden">
            <div class="title-bar rounded-none border-x-0 border-t-0">Phase resources</div>
            <ul class="divide-y divide-[var(--xp-border)] text-sm">
              @for (r of inheritedResources(); track r.id) {
                <li class="flex items-center justify-between gap-2 px-3 py-2">
                  <div>
                    <a [href]="r.url" target="_blank" rel="noopener" class="link">{{ r.title }}</a>
                    <p class="text-xs" style="color: var(--text-muted)">
                      {{ r.resource_type }} · {{ r.priority }}
                      @if (r.author) {
                        · {{ r.author }}
                      }
                    </p>
                  </div>
                  <button
                    type="button"
                    class="input-field !w-auto text-xs"
                    (click)="toggleInherited(r)"
                  >
                    {{ r.is_consumed ? 'Consumed' : 'Mark done' }}
                  </button>
                </li>
              }
            </ul>
          </div>
        }

        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Knowledge notes</div>
          @if (notes().length === 0) {
            <p class="p-3 text-sm" style="color: var(--text-muted)">No notes attached yet.</p>
          } @else {
            <ul class="divide-y divide-[var(--xp-border)] text-sm">
              @for (n of notes(); track n.id) {
                <li class="flex items-start justify-between gap-2 px-3 py-2">
                  <div>
                    <a [routerLink]="n.route" class="link">{{ n.section_title }}</a>
                    <p class="text-xs" style="color: var(--text-muted)">
                      {{ n.subject_title }} · {{ n.chapter_title }}
                    </p>
                    @if (n.snippet) {
                      <p class="text-xs mt-1">{{ n.snippet }}</p>
                    }
                  </div>
                  <button type="button" class="input-field !w-auto text-xs" (click)="detachNote(n)">
                    Unlink
                  </button>
                </li>
              }
            </ul>
          }
          <form
            class="space-y-2 border-t border-[var(--xp-border)] p-3 text-sm"
            [formGroup]="noteForm"
            (ngSubmit)="addNote()"
          >
            <label class="block">
              <span class="text-xs" style="color: var(--text-muted)">Subject</span>
              <select class="input-field" formControlName="subject_id">
                <option value="">＋ New subject…</option>
                @for (s of subjects(); track s.id) {
                  <option [value]="s.id">{{ s.title }}</option>
                }
              </select>
            </label>
            @if (!noteForm.controls.subject_id.value) {
              <label class="block">
                <span class="text-xs" style="color: var(--text-muted)">New subject name</span>
                <input class="input-field" formControlName="subject_title" placeholder="AI Systems Engineering" />
              </label>
            }
            <label class="block">
              <span class="text-xs" style="color: var(--text-muted)">Note title</span>
              <input class="input-field" formControlName="title" [placeholder]="concept()!.title" />
            </label>
            <label class="block">
              <span class="text-xs" style="color: var(--text-muted)">Note</span>
              <textarea
                class="input-field"
                rows="4"
                formControlName="content"
                placeholder="Explain it in your own words — that is the depth gate."
              ></textarea>
            </label>
            <button type="submit" class="btn-primary text-xs" [disabled]="savingNote()">
              Add note
            </button>
          </form>
        </div>

        <div class="panel !p-0 overflow-hidden">
          <div class="title-bar rounded-none border-x-0 border-t-0">Sessions</div>
          @if (sessions().length === 0) {
            <p class="p-3 text-sm" style="color: var(--text-muted)">No sessions logged yet.</p>
          } @else {
            <ul class="divide-y divide-[var(--xp-border)] text-sm">
              @for (s of sessions(); track s.id) {
                <li class="px-3 py-2">
                  <span>{{ s.session_date }}</span>
                  <span style="color: var(--text-muted)"> · {{ s.minutes }} min · conf {{ s.confidence }}</span>
                  @if (s.notes) {
                    <p class="text-xs mt-1">{{ s.notes }}</p>
                  }
                </li>
              }
            </ul>
          }
        </div>
      }
    </div>
  `,
})
export class LearningConceptDetailComponent implements OnInit {
  private readonly learningService = inject(LearningService);
  private readonly knowledgeService = inject(KnowledgeNotesService);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);
  concept = signal<LearningConcept | null>(null);
  resources = signal<LearningResource[]>([]);
  inheritedResources = signal<LearningResource[]>([]);
  sessions = signal<StudySession[]>([]);
  notes = signal<ConceptNote[]>([]);
  subjects = signal<KnowledgeSubjectListItem[]>([]);
  loading = signal(false);
  saving = signal(false);
  savingNote = signal(false);
  gateForm = this.fb.nonNullable.group({
    can_explain: [false],
    failure_modes_known: [false],
    tradeoffs_known: [false],
    confidence: [0],
    artifact_url: [''],
  });
  noteForm = this.fb.nonNullable.group({
    subject_id: [''],
    subject_title: [''],
    title: [''],
    content: [''],
  });

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) return;
    this.loading.set(true);
    this.learningService.getConcept(id).subscribe({
      next: (c) => {
        this.concept.set(c);
        this.resources.set(c.resources ?? []);
        this.inheritedResources.set(c.inherited_resources ?? []);
        this.gateForm.patchValue({
          can_explain: c.can_explain,
          failure_modes_known: c.failure_modes_known,
          tradeoffs_known: c.tradeoffs_known,
          confidence: c.confidence,
          artifact_url: c.artifact_url ?? '',
        });
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
    this.learningService.listSessions().subscribe({
      next: (all) => this.sessions.set(all.filter((s) => s.concept_id === id)),
    });
    this.knowledgeService.listSubjects().subscribe({ next: (s) => this.subjects.set(s) });
    this.loadNotes(id);
  }

  private loadNotes(conceptId: string): void {
    this.learningService.listConceptNotes(conceptId).subscribe({
      next: (list) => {
        this.notes.set(list);
        // Keep writing into the subject already used for this concept.
        if (list.length && !this.noteForm.controls.subject_id.value) {
          this.noteForm.patchValue({ subject_id: list[list.length - 1].subject_id });
        }
      },
    });
  }

  addNote(): void {
    const c = this.concept();
    if (!c) return;
    const raw = this.noteForm.getRawValue();
    if (!raw.subject_id && !raw.subject_title.trim()) return;
    this.savingNote.set(true);
    this.learningService
      .attachConceptNote(c.id, {
        subject_id: raw.subject_id || null,
        subject_title: raw.subject_id ? null : raw.subject_title.trim(),
        title: raw.title.trim() || c.title,
        content: raw.content,
      })
      .subscribe({
        next: (note) => {
          this.notes.update((list) => [...list, note]);
          this.noteForm.patchValue({ subject_id: note.subject_id, subject_title: '', title: '', content: '' });
          this.knowledgeService.listSubjects().subscribe({ next: (s) => this.subjects.set(s) });
          this.savingNote.set(false);
        },
        error: () => this.savingNote.set(false),
      });
  }

  detachNote(note: ConceptNote): void {
    const c = this.concept();
    if (!c) return;
    this.learningService.detachConceptNote(c.id, note.id).subscribe({
      next: () => this.notes.update((list) => list.filter((n) => n.id !== note.id)),
    });
  }

  toggleInherited(r: LearningResource): void {
    this.learningService.updateResource(r.id, { is_consumed: !r.is_consumed }).subscribe({
      next: (updated) => {
        this.inheritedResources.update((list) =>
          list.map((x) => (x.id === updated.id ? updated : x)),
        );
      },
    });
  }

  saveGate(): void {
    const c = this.concept();
    if (!c) return;
    this.saving.set(true);
    const raw = this.gateForm.getRawValue();
    this.learningService
      .updateConcept(c.id, {
        can_explain: raw.can_explain,
        failure_modes_known: raw.failure_modes_known,
        tradeoffs_known: raw.tradeoffs_known,
        confidence: raw.confidence,
        artifact_url: raw.artifact_url || null,
      })
      .subscribe({
        next: (updated) => {
          this.concept.set(updated);
          this.saving.set(false);
        },
        error: () => this.saving.set(false),
      });
  }

  toggleConsumed(r: LearningResource): void {
    this.learningService.updateResource(r.id, { is_consumed: !r.is_consumed }).subscribe({
      next: (updated) => {
        this.resources.update((list) => list.map((x) => (x.id === updated.id ? updated : x)));
      },
    });
  }
}
