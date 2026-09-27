import { Component, Input, OnChanges, OnDestroy, SimpleChanges, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { Subscription } from 'rxjs';
import { CodeWorkspaceComponent } from '../../../shared/code-workspace';
import { DsaNoteScope } from '../models/dsa.models';
import { DsaService } from '../services/dsa.service';
import { DsaStateComponent } from './dsa-state.component';

type SaveState = 'idle' | 'saving' | 'saved' | 'error';

/**
 * A user's private markdown note on a pattern or problem, in the same editor as journal and
 * knowledge notes. Autosaves after a pause in typing, and once more when the editor is closed.
 */
@Component({
  selector: 'app-dsa-note-editor',
  standalone: true,
  imports: [CodeWorkspaceComponent, DatePipe, DsaStateComponent],
  styles: [
    `
      .dsa-note-frame {
        min-height: 320px;
        height: 52vh;
        overflow: hidden;
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
      }
    `,
  ],
  template: `
    @if (loadError()) {
      <app-dsa-state title="We couldn't load your note." [retryable]="true" (retry)="load()" />
    } @else if (loaded()) {
      <div class="space-y-2" data-testid="dsa-note-editor">
        <div class="dsa-note-frame">
          <app-code-workspace
            [content]="initialContent"
            mode="markdown"
            language="markdown"
            [showPreview]="true"
            [showToolbar]="true"
            [showRunButton]="false"
            [showLanguageSelector]="false"
            [showOutput]="false"
            [enableAutosave]="true"
            defaultViewMode="write"
            (contentChange)="onContentChange($event)"
            (save)="persist()"
          />
        </div>
        <p class="text-xs" style="color: var(--text-muted)" data-testid="dsa-note-status" aria-live="polite">
          @switch (saveState()) {
            @case ('saving') { Saving… }
            @case ('error') { <span style="color: var(--danger)">Couldn't save. Your text is kept here; keep typing to retry.</span> }
            @default {
              @if (savedAt(); as at) { Saved {{ at | date: 'short' }} } @else { Private to you. Saved automatically. }
            }
          }
        </p>
      </div>
    } @else {
      <div class="panel--flat skeleton h-40"></div>
    }
  `,
})
export class DsaNoteEditorComponent implements OnChanges, OnDestroy {
  private readonly dsa = inject(DsaService);

  @Input({ required: true }) scope!: DsaNoteScope;
  @Input({ required: true }) slug!: string;

  readonly loaded = signal(false);
  readonly loadError = signal(false);
  readonly saveState = signal<SaveState>('idle');
  readonly savedAt = signal<string | null>(null);

  /** Content handed to the editor once per load; later edits live in `draft`. */
  initialContent = '';
  private draft = '';
  private saved = '';
  /** The note that is loaded. Inputs may already point at the next one when we flush, so saves use this. */
  private target: { scope: DsaNoteScope; slug: string } | null = null;
  private loadSub?: Subscription;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['scope'] || changes['slug']) {
      this.persist(); // save the previous note's unsaved text first
      this.load();
    }
  }

  ngOnDestroy(): void {
    this.loadSub?.unsubscribe();
    this.persist(); // tab switch or navigation: don't lose unsaved text
  }

  load(): void {
    this.loadSub?.unsubscribe();
    this.target = null;
    this.loaded.set(false);
    this.loadError.set(false);
    this.saveState.set('idle');
    const target = { scope: this.scope, slug: this.slug };
    this.loadSub = this.dsa.note(target.scope, target.slug).subscribe({
      next: (note) => {
        this.target = target;
        this.initialContent = this.draft = this.saved = note.content;
        this.savedAt.set(note.updated_at);
        this.loaded.set(true);
      },
      error: () => this.loadError.set(true),
    });
  }

  onContentChange(content: string): void {
    this.draft = content;
  }

  persist(): void {
    const target = this.target;
    if (!target || this.draft === this.saved) return;
    const content = this.draft;
    this.saveState.set('saving');
    this.dsa.saveNote(target.scope, target.slug, content).subscribe({
      next: (note) => {
        if (this.target !== target) return; // finished after we moved on to another note
        this.saved = content;
        this.savedAt.set(note.updated_at);
        this.saveState.set(this.draft === content ? 'saved' : 'idle');
      },
      error: () => {
        if (this.target === target) this.saveState.set('error');
      },
    });
  }
}
