import { DatePipe } from '@angular/common';
import {
  AfterViewInit,
  Component,
  DestroyRef,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  ViewChild,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { LucideDynamicIcon } from '@lucide/angular';
import { Subject, debounceTime } from 'rxjs';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import {
  STICKY_NOTES_PURGE_AFTER_DAYS,
  STICKY_NOTE_COLORS,
  StickyNote,
  StickyNoteColor,
  normalizeTag,
  stickyNoteDisplayTitle,
} from '../models/sticky-note.models';
import { StickyNoteUpdate, StickyNotesService } from '../services/sticky-notes.service';

const AUTOSAVE_DEBOUNCE_MS = 1500;

/**
 * Note editor popup, styled and behaving like Google Keep's note card:
 * the whole popup is tinted with the note's color, title/content are
 * borderless and auto-grow, the color palette hides behind a swatch
 * button, and the only chrome in the header is the pin toggle + close.
 */
@Component({
  selector: 'app-sticky-note-editor-modal',
  standalone: true,
  imports: [DatePipe, ModalComponent, LucideDynamicIcon],
  template: `
    <app-modal
      [open]="open"
      title=""
      [plain]="true"
      [background]="'var(--note-' + color() + ')'"
      maxWidth="480px"
      [hasFooter]="true"
      [closeOnBackdrop]="false"
      [resizable]="true"
      resizeStorageKey="sticky-note-editor-size"
      [resizeMinWidth]="320"
      [resizeMinHeight]="240"
      [resizeMaxWidth]="900"
      [resizeMaxHeight]="820"
      (closed)="onClose()"
    >
      <ng-container headerActions>
        <button
          type="button"
          class="modal-header__btn"
          [style.color]="isPinned() ? 'var(--primary)' : null"
          title="Pin note"
          aria-label="Pin note"
          (click)="togglePin()"
        >
          <svg class="h-4 w-4" lucideIcon="pin" [attr.fill]="isPinned() ? 'currentColor' : 'none'" aria-hidden="true"></svg>
        </button>
      </ng-container>

      <ng-container body>
        <input
          #titleInput
          type="text"
          class="mb-1 block w-full border-0 bg-transparent px-0 text-base font-medium text-[var(--text)] outline-none placeholder:text-[var(--text-faint)]"
          placeholder="Title"
          [value]="title()"
          (input)="onTitleInput($event)"
        />
        <textarea
          #contentInput
          rows="1"
          class="block w-full resize-none overflow-hidden border-0 bg-transparent px-0 text-sm text-[var(--text)] outline-none placeholder:text-[var(--text-faint)]"
          placeholder="Take a note…"
          [value]="content()"
          (input)="onContentInput($event)"
        ></textarea>

        <div class="mt-2 flex flex-wrap items-center gap-1.5">
          @for (tag of tags(); track tag) {
            <span class="inline-flex items-center gap-1 rounded-full border border-[var(--border)] bg-[var(--surface)]/70 px-2 py-0.5 text-xs text-[var(--text)]">
              #{{ tag }}
              <button
                type="button"
                class="leading-none text-[var(--text-faint)] hover:text-[var(--text)]"
                [attr.aria-label]="'Remove tag ' + tag"
                title="Remove tag"
                (click)="removeTag(tag)"
              >✕</button>
            </span>
          }
          <input
            #tagInput
            type="text"
            class="min-w-[90px] flex-1 border-0 bg-transparent px-0 py-0.5 text-xs text-[var(--text)] outline-none placeholder:text-[var(--text-faint)]"
            [placeholder]="tags().length ? '' : 'Add tag…'"
            [value]="tagDraft"
            (input)="onTagDraftInput($event)"
            (keydown)="onTagKeydown($event)"
            (blur)="onTagBlur()"
          />
        </div>
      </ng-container>

      <ng-container footer>
        <div class="flex items-center gap-1">
          <div class="relative">
            <button
              type="button"
              class="modal-header__btn"
              title="Change color"
              aria-label="Change color"
              (click)="colorMenuOpen = !colorMenuOpen"
            >
              <svg class="h-4 w-4" lucideIcon="palette" aria-hidden="true"></svg>
            </button>
            @if (colorMenuOpen) {
              <div class="absolute bottom-full left-0 z-10 mb-1 flex gap-1.5 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-2 shadow-[var(--shadow-md)]">
                @for (c of colors; track c.value) {
                  <button
                    type="button"
                    class="h-6 w-6 rounded-full border-2"
                    [style.background]="'var(--note-' + c.value + ')'"
                    [style.borderColor]="color() === c.value ? 'var(--primary)' : 'var(--border)'"
                    [attr.aria-label]="c.label"
                    [attr.aria-pressed]="color() === c.value"
                    [title]="c.label"
                    (click)="setColor(c.value)"
                  ></button>
                }
              </div>
            }
          </div>
          @if (note?.id) {
            <div class="relative">
              <button
                type="button"
                class="modal-header__btn"
                title="More"
                aria-label="More options"
                (click)="moreMenuOpen = !moreMenuOpen"
              >
                <svg class="h-4 w-4" lucideIcon="ellipsis-vertical" aria-hidden="true"></svg>
              </button>
              @if (moreMenuOpen) {
                <div class="absolute bottom-full left-0 z-10 mb-1 min-w-[140px] rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-1 shadow-[var(--shadow-md)]">
                  <button
                    type="button"
                    class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm text-[var(--text)] hover:bg-[var(--surface-3)]"
                    (click)="moreMenuOpen = false; onDelete()"
                  >
                    <svg class="h-4 w-4" lucideIcon="trash-2" aria-hidden="true"></svg>
                    Delete note
                  </button>
                </div>
              }
            </div>
          }
        </div>

        <div class="flex items-center gap-2 text-xs text-[var(--text-muted)]">
          <span aria-live="polite">{{ saveStatusLabel() }}</span>
          @if (note?.updated_at) {
            <span>Edited {{ note!.updated_at | date: 'MMM d, h:mm a' }}</span>
          }
          <button
            type="button"
            class="rounded px-2.5 py-1 text-xs font-medium text-[var(--text)] hover:bg-[var(--surface-3)]"
            (click)="onClose()"
          >Close</button>
        </div>
      </ng-container>
    </app-modal>
  `,
})
export class StickyNoteEditorModalComponent implements AfterViewInit, OnChanges {
  @Input() open = false;
  @Input() note: StickyNote | null = null;

  @Output() closed = new EventEmitter<void>();
  @Output() created = new EventEmitter<StickyNote>();
  @Output() updated = new EventEmitter<StickyNote>();
  @Output() deleted = new EventEmitter<string>();

  @ViewChild('titleInput') titleInputRef?: ElementRef<HTMLInputElement>;
  @ViewChild('contentInput') contentInputRef?: ElementRef<HTMLTextAreaElement>;
  @ViewChild('tagInput') tagInputRef?: ElementRef<HTMLInputElement>;

  private readonly service = inject(StickyNotesService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly confirmService = inject(ConfirmService);

  readonly colors = STICKY_NOTE_COLORS;
  readonly purgeAfterDays = STICKY_NOTES_PURGE_AFTER_DAYS;
  colorMenuOpen = false;
  moreMenuOpen = false;

  readonly title = signal('');
  readonly content = signal('');
  readonly color = signal<StickyNoteColor>('yellow');
  readonly isPinned = signal(false);
  readonly tags = signal<string[]>([]);
  readonly saveStatus = signal<'idle' | 'saving' | 'saved'>('idle');
  tagDraft = '';

  private readonly dirty$ = new Subject<void>();
  private focused = false;
  /** id of the note whose text is currently loaded into title()/content(); undefined = not yet loaded this open. */
  private syncedNoteId: string | null | undefined = undefined;

  constructor() {
    this.dirty$.pipe(debounceTime(AUTOSAVE_DEBOUNCE_MS), takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.save();
    });
  }

  ngAfterViewInit(): void {
    this.syncFromInput();
  }

  ngOnChanges(): void {
    this.syncFromInput();
  }

  private syncFromInput(): void {
    this.colorMenuOpen = false;
    this.moreMenuOpen = false;
    if (!this.open) {
      this.focused = false;
      this.syncedNoteId = undefined;
      return;
    }
    // Only reload title/content when a genuinely different note is being shown.
    // A `note` input change while open is otherwise just this component's own
    // save() response coming back — resyncing then would clobber keystrokes
    // typed during the network round-trip.
    const incomingId = this.note?.id ?? null;
    if (incomingId !== this.syncedNoteId) {
      this.title.set(this.note?.title ?? '');
      this.content.set(this.note?.content ?? '');
      this.color.set((this.note?.color as StickyNoteColor) ?? 'yellow');
      this.isPinned.set(this.note?.is_pinned ?? false);
      this.tags.set(this.note?.tags ?? []);
      this.tagDraft = '';
      this.saveStatus.set('idle');
      this.syncedNoteId = incomingId;
    }
    if (!this.focused) {
      this.focused = true;
      queueMicrotask(() => {
        this.contentInputRef?.nativeElement.focus();
        this.autoGrow();
      });
    }
  }

  private autoGrow(): void {
    const el = this.contentInputRef?.nativeElement;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.max(el.scrollHeight, 96)}px`;
  }

  saveStatusLabel(): string {
    switch (this.saveStatus()) {
      case 'saving':
        return 'Saving…';
      case 'saved':
        return 'Saved';
      default:
        return '';
    }
  }

  onTitleInput(event: Event): void {
    this.title.set((event.target as HTMLInputElement).value);
    this.dirty$.next();
  }

  onContentInput(event: Event): void {
    this.content.set((event.target as HTMLTextAreaElement).value);
    this.autoGrow();
    this.dirty$.next();
  }

  setColor(color: StickyNoteColor): void {
    this.color.set(color);
    this.colorMenuOpen = false;
    // Only persist immediately if the note already exists — choosing a
    // color before typing anything shouldn't create an empty note.
    if (this.note?.id) this.patchExisting({ color });
  }

  togglePin(): void {
    const next = !this.isPinned();
    this.isPinned.set(next);
    if (this.note?.id) this.patchExisting({ is_pinned: next });
  }

  async onDelete(): Promise<void> {
    const id = this.note?.id;
    if (!id) return;
    const label = stickyNoteDisplayTitle({ title: this.title(), content: this.content() });
    const ok = await this.confirmService.confirm(
      `Delete "${label}"? It will be hidden now and permanently removed after ${this.purgeAfterDays} days.`,
      'Delete note',
    );
    if (!ok) return;
    this.service.delete(id).subscribe(() => {
      this.deleted.emit(id);
      this.closed.emit();
    });
  }

  onClose(): void {
    this.commitTagDraft();
    if (this.isDirty()) this.save();
    this.closed.emit();
  }

  private isDirty(): boolean {
    if (!this.note) {
      return this.title().trim().length > 0 || this.content().trim().length > 0 || this.tags().length > 0;
    }
    return (
      this.title() !== (this.note.title ?? '') ||
      this.content() !== (this.note.content ?? '') ||
      !this.tagsEqual(this.tags(), this.note.tags ?? [])
    );
  }

  private tagsEqual(a: string[], b: string[]): boolean {
    return a.length === b.length && a.every((t, i) => t === b[i]);
  }

  /** Debounced autosave while typing: creates the note on first non-blank input, updates it after. */
  private save(): void {
    if (!this.isDirty()) return;
    const title = this.title().trim() || null;
    const content = this.content();
    const tags = this.tags();
    if (this.note?.id) {
      this.patchExisting({ title, content, tags });
      return;
    }
    // Tags alone are enough to create a note — tagging is an intentional act.
    if (!title && !content.trim() && tags.length === 0) return;
    this.saveStatus.set('saving');
    this.service
      .create({ title, content, color: this.color(), is_pinned: this.isPinned(), tags })
      .subscribe((created) => {
        this.note = created;
        this.tags.set(created.tags ?? []);
        this.saveStatus.set('saved');
        this.created.emit(created);
      });
  }

  onTagDraftInput(event: Event): void {
    this.tagDraft = (event.target as HTMLInputElement).value;
  }

  onTagKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault();
      this.commitTagDraft();
      this.persistTags();
    } else if (event.key === 'Backspace' && !this.tagDraft && this.tags().length > 0) {
      this.removeTag(this.tags()[this.tags().length - 1]);
    }
  }

  onTagBlur(): void {
    this.commitTagDraft();
    this.persistTags();
  }

  /** Folds any in-progress tag text into tags() without persisting — callers persist afterwards. */
  private commitTagDraft(): void {
    const raw = this.tagDraft;
    this.tagDraft = '';
    if (this.tagInputRef) this.tagInputRef.nativeElement.value = '';
    const tag = normalizeTag(raw);
    if (!tag || this.tags().includes(tag)) return;
    this.tags.set([...this.tags(), tag]);
  }

  removeTag(tag: string): void {
    this.tags.set(this.tags().filter((t) => t !== tag));
    this.persistTags();
  }

  /** Tag chips change is a discrete action — persist immediately rather than waiting on the debounce. */
  private persistTags(): void {
    if (this.note?.id) {
      this.patchExisting({ tags: this.tags() });
    } else {
      this.save();
    }
  }

  /** Immediate PATCH for a note that already exists. */
  private patchExisting(payload: StickyNoteUpdate): void {
    if (!this.note?.id) return;
    this.saveStatus.set('saving');
    this.service.update(this.note.id, payload).subscribe((updated) => {
      this.note = updated;
      this.saveStatus.set('saved');
      this.updated.emit(updated);
    });
  }
}
