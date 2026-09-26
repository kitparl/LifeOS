import { CdkDrag, CdkDragDrop, CdkDropList, moveItemInArray } from '@angular/cdk/drag-drop';
import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { LucideDynamicIcon } from '@lucide/angular';
import { Subject, debounceTime, distinctUntilChanged, forkJoin } from 'rxjs';
import { MONTH_OPTIONS } from '../../core/constants/months';
import { ConfirmService } from '../../shared/confirm/confirm.service';
import { StickyNoteCardComponent } from './components/sticky-note-card.component';
import { StickyNoteEditorModalComponent } from './components/sticky-note-editor-modal.component';
import {
  STICKY_NOTES_PURGE_AFTER_DAYS,
  StickyNote,
  StickyNoteMonth,
  stickyNoteDisplayTitle,
  stickyNoteMonthLabel,
  stickyNoteYearOptions,
} from './models/sticky-note.models';
import { StickyNotesService } from './services/sticky-notes.service';
import { yearMonthKey } from '../../core/utils/date';

type NotesView = 'period' | 'all' | 'deleted';

@Component({
  selector: 'app-sticky-notes-page',
  standalone: true,
  imports: [CdkDropList, CdkDrag, FormsModule, LucideDynamicIcon, StickyNoteCardComponent, StickyNoteEditorModalComponent],
  template: `
    <div class="safe-x safe-bottom space-y-4 pb-24">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex flex-wrap items-center gap-2 text-xs" style="color: var(--text-muted)">
          <button
            type="button"
            class="btn-secondary !px-2 text-xs"
            title="Previous month"
            aria-label="Previous month"
            [disabled]="!isPeriodView()"
            (click)="stepMonth(-1)"
          >
            <svg class="h-4 w-4" lucideIcon="chevron-left" aria-hidden="true"></svg>
          </button>

          <label class="flex items-center gap-1.5" for="sticky-notes-year-select">
            <span>Year:</span>
            <select
              id="sticky-notes-year-select"
              class="input-field !w-auto !py-1 text-xs"
              data-testid="sticky-notes-year-filter"
              [disabled]="!isPeriodView()"
              [ngModel]="year()"
              (ngModelChange)="onYearPicked($event)"
            >
              @for (option of yearOptions(); track option) {
                <option [ngValue]="option">{{ option }}</option>
              }
            </select>
          </label>

          <label class="flex items-center gap-1.5" for="sticky-notes-month-select">
            <span>Month:</span>
            <select
              id="sticky-notes-month-select"
              class="input-field !w-auto !py-1 text-xs"
              data-testid="sticky-notes-month-filter"
              [disabled]="!isPeriodView()"
              [ngModel]="month()"
              (ngModelChange)="onMonthPicked($event)"
            >
              @for (option of monthOptions; track option.value) {
                <option [ngValue]="option.value">{{ option.label }}</option>
              }
            </select>
          </label>

          <button
            type="button"
            class="btn-secondary !px-2 text-xs"
            title="Next month"
            aria-label="Next month"
            [disabled]="!isPeriodView()"
            (click)="stepMonth(1)"
          >
            <svg class="h-4 w-4" lucideIcon="chevron-right" aria-hidden="true"></svg>
          </button>

          <label class="flex items-center gap-1.5" for="sticky-notes-view-select">
            <span>Show:</span>
            <select
              id="sticky-notes-view-select"
              class="input-field !w-auto !py-1 text-xs"
              data-testid="sticky-notes-view-filter"
              [ngModel]="view()"
              (ngModelChange)="onViewPicked($event)"
            >
              <option [ngValue]="'period'">Selected month</option>
              <option [ngValue]="'all'">All Notes</option>
              <option [ngValue]="'deleted'">Deleted</option>
            </select>
          </label>
        </div>

        <div class="relative min-w-[180px] flex-1 sm:flex-none">
          <svg class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-faint)]" lucideIcon="search" aria-hidden="true"></svg>
          <input
            type="search"
            class="input-field w-full text-sm"
            style="padding-left: 2.25rem"
            placeholder="Search notes or #tags…"
            [value]="searchQuery()"
            (input)="onSearchInput($event)"
          />
        </div>
      </div>

      @if (loading()) {
        <p class="text-sm" style="color: var(--text-muted)">Loading…</p>
      } @else if (isSearching()) {
        <div>
          <p class="mb-2 text-xs" style="color: var(--text-muted)">
            {{ searchResults().length }} result(s) for "{{ searchQuery() }}"
          </p>
          @if (searchResults().length === 0) {
            <div class="panel"><p class="text-sm" style="color: var(--text-muted)">No notes match your search.</p></div>
          } @else {
            <div class="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              @for (note of searchResults(); track note.id) {
                <app-sticky-note-card [note]="note" [draggable]="false" (open)="openNote(note)" (togglePin)="togglePin(note)" (colorChange)="changeColor(note, $event)" (deleteNote)="deleteNote(note)" />
              }
            </div>
          }
        </div>
      } @else if (isAllView()) {
        @if (notes().length === 0) {
          <div class="panel text-center">
            <p class="text-sm" style="color: var(--text-muted)">No notes yet.</p>
            <button type="button" class="btn-primary mt-2 text-xs" (click)="openNewNote()">New note</button>
          </div>
        } @else {
          <div class="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            @for (note of notes(); track note.id) {
              <app-sticky-note-card [note]="note" [draggable]="false" (open)="openNote(note)" (togglePin)="togglePin(note)" (colorChange)="changeColor(note, $event)" (deleteNote)="deleteNote(note)" />
            }
          </div>
        }
      } @else if (isDeletedView()) {
        <p class="mb-2 text-xs" style="color: var(--text-muted)">
          Deleted notes are kept for {{ purgeAfterDays }} days, then permanently removed.
        </p>
        @if (notes().length === 0) {
          <div class="panel"><p class="text-sm" style="color: var(--text-muted)">No deleted notes.</p></div>
        } @else {
          <div class="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            @for (note of notes(); track note.id) {
              <app-sticky-note-card [note]="note" [draggable]="false" [deletedMode]="true" (restore)="restoreNote(note)" />
            }
          </div>
        }
      } @else {
        @if (pinnedNotes().length > 0) {
          <div>
            <p class="mb-2 flex items-center gap-1 text-xs font-medium" style="color: var(--text-muted)">
              <svg class="h-3.5 w-3.5" lucideIcon="pin" fill="currentColor" aria-hidden="true"></svg>
              Pinned
            </p>
            <div cdkDropList [cdkDropListData]="pinnedNotes()" (cdkDropListDropped)="onDrop('pinned', $event)" class="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              @for (note of pinnedNotes(); track note.id) {
                <div cdkDrag [cdkDragData]="note">
                  <app-sticky-note-card [note]="note" (open)="openNote(note)" (togglePin)="togglePin(note)" (colorChange)="changeColor(note, $event)" (deleteNote)="deleteNote(note)" />
                </div>
              }
            </div>
          </div>
        }

        <div>
          @if (pinnedNotes().length > 0) {
            <p class="mb-2 text-xs font-medium" style="color: var(--text-muted)">Notes</p>
          }
          @if (unpinnedNotes().length === 0 && pinnedNotes().length === 0) {
            <div class="panel text-center">
              <p class="text-sm" style="color: var(--text-muted)">No notes in {{ periodLabel() }} yet.</p>
              <button type="button" class="btn-primary mt-2 text-xs" (click)="openNewNote()">New note</button>
            </div>
          } @else {
            <div cdkDropList [cdkDropListData]="unpinnedNotes()" (cdkDropListDropped)="onDrop('notes', $event)" class="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              @for (note of unpinnedNotes(); track note.id) {
                <div cdkDrag [cdkDragData]="note">
                  <app-sticky-note-card [note]="note" (open)="openNote(note)" (togglePin)="togglePin(note)" (colorChange)="changeColor(note, $event)" (deleteNote)="deleteNote(note)" />
                </div>
              }
            </div>
          }
        </div>
      }
    </div>

    <button
      type="button"
      class="btn-primary fixed bottom-6 right-6 z-20 flex h-12 w-12 items-center justify-center rounded-full !p-0 shadow-[var(--shadow-lg)]"
      title="New note"
      aria-label="New note"
      (click)="openNewNote()"
    >
      <svg class="h-5 w-5" lucideIcon="plus" aria-hidden="true"></svg>
    </button>

    <app-sticky-note-editor-modal
      [open]="editorOpen()"
      [note]="selectedNote()"
      (closed)="onEditorClosed()"
      (created)="onNoteCreated($event)"
      (updated)="onNoteUpdated($event)"
      (deleted)="onNoteDeleted($event)"
    />
  `,
})
export class StickyNotesPageComponent implements OnInit {
  private readonly service = inject(StickyNotesService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly confirmService = inject(ConfirmService);

  readonly months = signal<StickyNoteMonth[]>([]);
  readonly year = signal(new Date().getFullYear());
  readonly month = signal(new Date().getMonth() + 1);
  readonly view = signal<NotesView>('period');
  readonly monthKey = computed(() => yearMonthKey(this.year(), this.month()));
  readonly isPeriodView = computed(() => this.view() === 'period');
  readonly isAllView = computed(() => this.view() === 'all');
  readonly isDeletedView = computed(() => this.view() === 'deleted');
  readonly notes = signal<StickyNote[]>([]);
  readonly loading = signal(false);
  readonly purgeAfterDays = STICKY_NOTES_PURGE_AFTER_DAYS;
  readonly monthOptions = MONTH_OPTIONS;
  readonly yearOptions = computed(() => stickyNoteYearOptions(this.months(), this.year()));

  readonly searchQuery = signal('');
  readonly searchResults = signal<StickyNote[]>([]);
  readonly isSearching = () => this.searchQuery().trim().length > 0;

  readonly editorOpen = signal(false);
  readonly selectedNote = signal<StickyNote | null>(null);

  readonly pinnedNotes = computed(() => this.notes().filter((n) => n.is_pinned));
  readonly unpinnedNotes = computed(() => this.notes().filter((n) => !n.is_pinned));

  private readonly search$ = new Subject<string>();

  ngOnInit(): void {
    this.loadMonths();
    this.loadMonthNotes(this.monthKey());

    this.search$.pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef)).subscribe((q) => {
      if (!q.trim()) {
        this.searchResults.set([]);
        return;
      }
      this.service.search(q).subscribe((results) => this.searchResults.set(results));
    });
  }

  periodLabel(): string {
    return stickyNoteMonthLabel(this.monthKey());
  }

  private loadMonths(): void {
    this.service.listMonths().subscribe((months) => this.months.set(months));
  }

  private loadMonthNotes(month: string): void {
    this.loading.set(true);
    this.service.listByMonth(month).subscribe((notes) => {
      this.notes.set(notes);
      this.loading.set(false);
    });
  }

  private loadAllNotes(): void {
    this.loading.set(true);
    this.service.listAll().subscribe((notes) => {
      this.notes.set(notes);
      this.loading.set(false);
    });
  }

  private loadDeletedNotes(): void {
    this.loading.set(true);
    this.service.listDeleted().subscribe((notes) => {
      this.notes.set(notes);
      this.loading.set(false);
    });
  }

  private applyPeriod(): void {
    this.view.set('period');
    this.loadMonthNotes(this.monthKey());
  }

  private applyView(view: NotesView): void {
    this.view.set(view);
    if (view === 'all') {
      this.loadAllNotes();
    } else if (view === 'deleted') {
      this.loadDeletedNotes();
    } else {
      this.loadMonthNotes(this.monthKey());
    }
  }

  stepMonth(delta: number): void {
    if (!this.isPeriodView()) return;
    const date = new Date(this.year(), this.month() - 1 + delta, 1);
    this.year.set(date.getFullYear());
    this.month.set(date.getMonth() + 1);
    this.applyPeriod();
  }

  onYearPicked(year: number): void {
    this.year.set(Number(year));
    this.applyPeriod();
  }

  onMonthPicked(month: number): void {
    this.month.set(Number(month));
    this.applyPeriod();
  }

  onViewPicked(view: NotesView): void {
    this.applyView(view);
  }

  onSearchInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.searchQuery.set(value);
    this.search$.next(value);
  }

  openNewNote(): void {
    this.selectedNote.set(null);
    this.editorOpen.set(true);
  }

  openNote(note: StickyNote): void {
    this.selectedNote.set(note);
    this.editorOpen.set(true);
  }

  togglePin(note: StickyNote): void {
    this.service.update(note.id, { is_pinned: !note.is_pinned }).subscribe((updated) => this.replaceNote(updated));
  }

  changeColor(note: StickyNote, color: StickyNote['color']): void {
    this.service.update(note.id, { color }).subscribe((updated) => this.replaceNote(updated));
  }

  async deleteNote(note: StickyNote): Promise<void> {
    const label = stickyNoteDisplayTitle(note);
    const ok = await this.confirmService.confirm(
      `Delete "${label}"? It will be hidden now and permanently removed after ${STICKY_NOTES_PURGE_AFTER_DAYS} days.`,
      'Delete note',
    );
    if (!ok) return;
    this.service.delete(note.id).subscribe(() => this.onNoteDeleted(note.id));
  }

  restoreNote(note: StickyNote): void {
    this.service.restore(note.id).subscribe(() => {
      this.notes.set(this.notes().filter((n) => n.id !== note.id));
      this.loadMonths();
    });
  }

  onDrop(section: 'pinned' | 'notes', event: CdkDragDrop<StickyNote[]>): void {
    if (event.previousIndex === event.currentIndex) return;
    moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
    const reordered = event.container.data;
    const others = this.notes().filter((n) => (section === 'pinned' ? !n.is_pinned : n.is_pinned));
    this.notes.set(section === 'pinned' ? [...reordered, ...others] : [...others, ...reordered]);

    const requests = reordered.map((note, index) => this.service.update(note.id, { order_index: index }));
    forkJoin(requests).subscribe((updated) => updated.forEach((n) => this.replaceNote(n, { silent: true })));
  }

  onEditorClosed(): void {
    this.editorOpen.set(false);
    this.selectedNote.set(null);
  }

  onNoteCreated(note: StickyNote): void {
    this.selectedNote.set(note);
    if (this.isAllView() || note.note_month === this.monthKey()) {
      this.notes.set([note, ...this.notes()]);
    }
    this.loadMonths();
  }

  onNoteUpdated(note: StickyNote): void {
    this.selectedNote.set(note);
    this.replaceNote(note);
  }

  onNoteDeleted(id: string): void {
    this.notes.set(this.notes().filter((n) => n.id !== id));
    this.editorOpen.set(false);
    this.selectedNote.set(null);
    this.loadMonths();
  }

  private replaceNote(note: StickyNote, opts: { silent?: boolean } = {}): void {
    this.notes.set(this.notes().map((n) => (n.id === note.id ? note : n)));
    if (!opts.silent && this.selectedNote()?.id === note.id) {
      this.selectedNote.set(note);
    }
  }
}
