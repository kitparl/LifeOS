import {
  CdkDrag,
  CdkDragDrop,
  CdkDragHandle,
  CdkDragPlaceholder,
  CdkDropList,
  moveItemInArray,
  transferArrayItem,
} from '@angular/cdk/drag-drop';
import { Component, DestroyRef, ElementRef, HostListener, AfterViewChecked, OnInit, ViewChild, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Subject, forkJoin } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { LucideCircle, LucideCircleCheck, LucideDynamicIcon, provideLucideIcons } from '@lucide/angular';
import { ConfirmService } from '../../shared/confirm/confirm.service';
import { MarkdownPipe } from '../../shared/markdown/markdown.pipe';
import { FileImageSrcDirective } from '../../shared/markdown/file-image-src.directive';
import { AttachmentListComponent } from '../files/components/attachment-list.component';
import { FileRecord } from '../files/models/file.models';
import { KnowledgeNotesEditorComponent } from './knowledge-notes-editor.component';
import {
  KnowledgeChapter,
  KnowledgeSearchHit,
  KnowledgeSection,
  KnowledgeSubjectDetail,
} from './models/knowledge-notes.models';
import { KnowledgeNotesService } from './services/knowledge-notes.service';

type SyncState = 'synced' | 'unsaved' | 'saving';
type RenameTarget = { kind: 'chapter' | 'section' | 'subject'; id: string };
type SearchGroup = { chapter_id: string; chapter_title: string; sections: KnowledgeSearchHit[] };

const SIDEBAR_KEY = 'lifeos.kn.sidebarWidth';
const EXPANDED_PREFIX = 'lifeos.kn.expanded.';
const LAST_SECTION_PREFIX = 'lifeos.kn.lastSection.';
const LAST_EDITED_PREFIX = 'lifeos.kn.lastEdited.';
const SIDEBAR_DEFAULT = 256;
const SIDEBAR_MIN = 180;
const SIDEBAR_MAX = 480;

@Component({
  selector: 'app-knowledge-subject',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    KnowledgeNotesEditorComponent,
    MarkdownPipe,
    FileImageSrcDirective,
    AttachmentListComponent,
    CdkDropList,
    CdkDrag,
    CdkDragHandle,
    CdkDragPlaceholder,
    LucideDynamicIcon,
  ],
  providers: [provideLucideIcons(LucideCircleCheck, LucideCircle)],
  template: `
    @if (subject(); as s) {
      <div class="space-y-2">
        <div class="kn-breadcrumb">
          <nav class="kn-breadcrumb__nav" aria-label="Notes">
            <a routerLink="/knowledge" class="kn-breadcrumb__link">← Notes</a>
            <span class="kn-breadcrumb__sep" aria-hidden="true">/</span>
            @if (renaming()?.kind === 'subject') {
              <input
                #renameInput
                type="text"
                class="kn-inline-input kn-inline-input--subject"
                [value]="s.title"
                aria-label="Rename subject"
                (keydown.enter)="commitRename($event)"
                (keydown.escape)="cancelRename()"
                (blur)="commitRename($event)"
              />
            } @else {
              <span
                class="kn-breadcrumb__current truncate"
                title="Double-click to rename"
                (dblclick)="startRename('subject', s.id, $event)"
              >{{ s.title }}</span>
            }
          </nav>
          <div class="kn-breadcrumb__tools">
            <div class="kn-subject-search">
              <input
                type="search"
                class="kn-subject-search__input input-field text-xs"
                placeholder="Search notes…"
                [value]="searchQuery()"
                aria-label="Search notes in this subject"
                (input)="onSearchInput($event)"
                (focus)="searchOpen.set(true)"
                (keydown.escape)="closeSearch()"
              />
              @if (searchOpen() && searchQuery().trim() && groupedSearchHits().length > 0) {
                <div class="kn-subject-search__results" role="listbox">
                  @for (group of groupedSearchHits(); track group.chapter_id) {
                    <div class="kn-subject-search__group">
                      <p class="kn-subject-search__chapter">{{ group.chapter_title }}</p>
                      @for (hit of group.sections; track hit.section_id) {
                        <button
                          type="button"
                          class="kn-subject-search__hit"
                          role="option"
                          (click)="openSearchHit(hit)"
                        >{{ hit.section_title }}</button>
                      }
                    </div>
                  }
                </div>
              } @else if (searchOpen() && searchQuery().trim() && searchLoaded()) {
                <div class="kn-subject-search__results kn-subject-search__results--empty">
                  <p class="text-xs" style="color: var(--text-muted)">No matches</p>
                </div>
              }
            </div>
            <div class="kn-overflow">
            <button
              type="button"
              class="btn-ghost kn-overflow__btn"
              aria-label="Subject actions"
              aria-haspopup="menu"
              [attr.aria-expanded]="openMenu() === 'subject'"
              (click)="toggleMenu('subject', $event)"
            >⋯</button>
            @if (openMenu() === 'subject') {
              <div class="menu kn-overflow__menu" role="menu" (click)="$event.stopPropagation()">
                <button type="button" class="menu-item" role="menuitem" (click)="startRename('subject', s.id); closeMenu()">Rename</button>
                <button type="button" class="menu-item menu-item--danger" role="menuitem" (click)="deleteSubject(); closeMenu()">Delete</button>
              </div>
            }
          </div>
          </div>
        </div>

        <div
          #layout
          class="kn-layout"
          [class.is-resizing]="resizing()"
          [style.--kn-sidebar-width.px]="sidebarWidth()"
        >
          <aside class="kn-sidebar">
            <div class="flex items-center justify-between px-1 pb-1">
              <span class="section-heading">Chapters</span>
              <button
                type="button"
                class="kn-plus"
                title="New chapter"
                aria-label="New chapter"
                (click)="addChapter()"
              >+</button>
            </div>
            @if (s.chapters.length === 0) {
              <p class="px-1 text-xs" style="color: var(--text-muted)">No chapters yet.</p>
            }
            <div
              class="kn-chapter-list"
              cdkDropList
              [cdkDropListData]="s.chapters"
              [cdkDropListConnectedTo]="noConnectedLists"
              (cdkDropListDropped)="onChapterDrop($event)"
            >
              @for (c of s.chapters; track c.id; let ci = $index) {
                <div class="kn-chapter" cdkDrag [cdkDragDisabled]="!!renaming()" [class.kn-chapter--closed]="!!c.closed_at">
                  <div class="kn-chapter__head">
                    <span class="kn-drag" title="Drag to reorder" aria-hidden="true" cdkDragHandle>⋮⋮</span>
                    <button
                      type="button"
                      class="kn-chapter__chevron"
                      [attr.aria-expanded]="isExpanded(c.id)"
                      [attr.aria-label]="isExpanded(c.id) ? 'Collapse chapter' : 'Expand chapter'"
                      (click)="toggleChapter(c, $event)"
                    >{{ isExpanded(c.id) ? '▼' : '▶' }}</button>
                    <span class="kn-index kn-index--chapter" aria-hidden="true">{{ ci + 1 }}</span>
                    <span class="kn-status-slot" aria-hidden="true">
                      @if (chapterStatus(c) === 'done') {
                        <svg class="kn-status-icon kn-status-icon--done" lucideIcon="circle-check" title="Completed"></svg>
                      } @else if (chapterStatus(c) === 'ongoing') {
                        <svg class="kn-status-icon kn-status-icon--ongoing" lucideIcon="circle" title="In progress"></svg>
                      }
                    </span>
                    @if (renaming()?.kind === 'chapter' && renaming()?.id === c.id) {
                      <input
                        #renameInput
                        type="text"
                        class="kn-inline-input"
                        [value]="c.title"
                        aria-label="Rename chapter"
                        (click)="$event.stopPropagation()"
                        (keydown.enter)="commitRename($event)"
                        (keydown.escape)="cancelRename()"
                        (blur)="commitRename($event)"
                      />
                    } @else {
                      <span
                        class="kn-chapter__title truncate"
                        [class.kn-closed]="!!c.closed_at"
                        title="Click to expand · double-click to rename"
                        (click)="onChapterClick(c, $event)"
                        (dblclick)="startRename('chapter', c.id, $event)"
                      >{{ c.title }}</span>
                    }
                    <button
                      type="button"
                      class="kn-plus kn-plus--row"
                      title="New section"
                      aria-label="New section"
                      (click)="addSection(c); $event.stopPropagation()"
                    >+</button>
                    <div class="kn-overflow kn-chapter__overflow" [class.is-open]="openMenu() === 'chapter:' + c.id">
                      <button
                        type="button"
                        class="kn-overflow__btn kn-overflow__btn--quiet"
                        aria-label="Chapter actions"
                        aria-haspopup="menu"
                        [attr.aria-expanded]="openMenu() === 'chapter:' + c.id"
                        (click)="toggleMenu('chapter:' + c.id, $event)"
                      >⋯</button>
                      @if (openMenu() === 'chapter:' + c.id) {
                        <div class="menu kn-overflow__menu" role="menu" (click)="$event.stopPropagation()">
                          <button type="button" class="menu-item" role="menuitem" (click)="startRename('chapter', c.id); closeMenu()">Rename</button>
                          @if (c.closed_at) {
                            <button type="button" class="menu-item" role="menuitem" (click)="toggleChapterClosed(c, false); closeMenu()">Reopen chapter</button>
                          } @else {
                            <button type="button" class="menu-item" role="menuitem" (click)="toggleChapterClosed(c, true); closeMenu()">Mark chapter completed</button>
                          }
                          <button type="button" class="menu-item menu-item--danger" role="menuitem" (click)="deleteChapter(c); closeMenu()">Delete</button>
                        </div>
                      }
                    </div>
                  </div>
                  @if (isExpanded(c.id)) {
                  <div
                    class="kn-section-list"
                    cdkDropList
                    [id]="sectionListId(c.id)"
                    [cdkDropListData]="c.sections"
                    [cdkDropListConnectedTo]="sectionListIds()"
                    (cdkDropListDropped)="onSectionDrop($event)"
                  >
                    @for (sec of c.sections; track sec.id) {
                      <div
                        class="kn-section-row"
                        cdkDrag
                        [cdkDragDisabled]="!!renaming()"
                        [class.active]="selected()?.id === sec.id"
                        [class.kn-section-row--closed]="!!sec.closed_at"
                      >
                        <span class="kn-drag" title="Drag to reorder" aria-hidden="true" cdkDragHandle>⋮⋮</span>
                        <span class="kn-status-slot" aria-hidden="true">
                          @if (sectionStatus(c, sec) === 'done') {
                            <svg class="kn-status-icon kn-status-icon--done" lucideIcon="circle-check" title="Completed"></svg>
                          } @else if (sectionStatus(c, sec) === 'ongoing') {
                            <svg class="kn-status-icon kn-status-icon--ongoing" lucideIcon="circle" title="In progress"></svg>
                          }
                        </span>
                        @if (renaming()?.kind === 'section' && renaming()?.id === sec.id) {
                          <input
                            #renameInput
                            type="text"
                            class="kn-inline-input"
                            [value]="sec.title"
                            aria-label="Rename section"
                            (click)="$event.stopPropagation()"
                            (keydown.enter)="commitRename($event)"
                            (keydown.escape)="cancelRename()"
                            (blur)="commitRename($event)"
                          />
                        } @else {
                          <button
                            type="button"
                            class="kn-section-link"
                            [class.active]="selected()?.id === sec.id"
                            [class.kn-closed]="!!sec.closed_at"
                            title="Double-click to rename"
                            (click)="selectSection(sec, c)"
                            (dblclick)="startRename('section', sec.id, $event)"
                          >{{ sec.title }}</button>
                        }
                        <button
                          type="button"
                          class="kn-section__delete"
                          title="Delete section"
                          aria-label="Delete section"
                          (click)="deleteSection(sec); $event.stopPropagation()"
                        >
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                          </svg>
                        </button>
                        <div *cdkDragPlaceholder class="kn-drag-placeholder"></div>
                      </div>
                    }
                  </div>
                  }
                  <div *cdkDragPlaceholder class="kn-drag-placeholder kn-drag-placeholder--chapter"></div>
                </div>
              }
            </div>
            @if (archivedSections().length > 0) {
              <div class="kn-archived">
                <p class="kn-archived__heading">Archived</p>
                @for (sec of archivedSections(); track sec.id) {
                  <div class="kn-archived__row">
                    <div class="min-w-0 flex-1">
                      <p class="kn-archived__title truncate">{{ sec.title }}</p>
                      <p class="kn-archived__meta">Deletes in {{ archiveDaysLeft(sec) }}d</p>
                    </div>
                    <button type="button" class="btn-ghost text-xs" (click)="restoreSection(sec)">Restore</button>
                    <button type="button" class="btn-ghost text-xs" (click)="deletePermanently(sec)">Delete</button>
                  </div>
                }
              </div>
            }
          </aside>

          <div
            class="kn-split-divider"
            role="separator"
            tabindex="0"
            aria-orientation="vertical"
            aria-label="Resize chapters sidebar"
            title="Drag to resize. Double-click to reset."
            (pointerdown)="onResizePointerDown($event)"
            (pointermove)="onResizePointerMove($event)"
            (pointerup)="onResizePointerUp($event)"
            (pointercancel)="onResizePointerUp($event)"
            (dblclick)="resetSidebarWidth()"
            (keydown)="onResizeKeydown($event)"
          ></div>

          <section class="kn-main">
            @if (selected(); as sec) {
              <form [formGroup]="form" class="space-y-2">
                <div class="kn-docbar">
                  @if (previewOnly()) {
                    <h2 class="kn-section-title-read">{{ form.controls.title.value }}</h2>
                  } @else {
                    <input class="kn-section-title" formControlName="title" placeholder="Section title" />
                  }
                  <div class="kn-docbar__actions">
                    @if (previewOnly()) {
                      <button type="button" class="btn-primary text-xs" (click)="enterEditMode()">Edit</button>
                    } @else {
                      <span class="kn-sync" [attr.data-state]="syncState()" aria-live="polite">
                        @switch (syncState()) {
                          @case ('saving') { Saving… }
                          @case ('unsaved') { Unsaved }
                          @default { Synced }
                        }
                      </span>
                      <button
                        type="button"
                        class="btn-primary text-xs"
                        [disabled]="syncState() !== 'unsaved'"
                        (click)="save()"
                      >Save</button>
                      <button type="button" class="btn-secondary text-xs" (click)="cancelEdit()">Cancel</button>
                    }
                    <div class="kn-overflow">
                      <button
                        type="button"
                        class="btn-ghost kn-overflow__btn"
                        aria-label="Section actions"
                        aria-haspopup="menu"
                        [attr.aria-expanded]="openMenu() === 'section'"
                        (click)="toggleMenu('section', $event)"
                      >⋯</button>
                      @if (openMenu() === 'section') {
                        <div class="menu kn-overflow__menu" role="menu" (click)="$event.stopPropagation()">
                          @if (sec.closed_at) {
                            <button type="button" class="menu-item" role="menuitem" (click)="toggleSectionClosed(sec, false); closeMenu()">Reopen section</button>
                          } @else {
                            <button type="button" class="menu-item" role="menuitem" (click)="toggleSectionClosed(sec, true); closeMenu()">Mark section completed</button>
                          }
                          <button type="button" class="menu-item menu-item--danger" role="menuitem" (click)="deleteSection(sec); closeMenu()">Delete</button>
                        </div>
                      }
                    </div>
                  </div>
                </div>
                @if (previewOnly()) {
                  <div class="markdown-body panel" appFileImageSrc [innerHTML]="form.controls.content.value | markdown"></div>
                } @else {
                  <app-knowledge-notes-editor
                    [section]="sec"
                    (contentChange)="onEditorContentChange($event)"
                    (sectionUpdated)="onEditorSaved($event)"
                    (saveRequested)="save()"
                    (editorReadyChange)="onEditorReady()"
                    (filesChanged)="onInlineFilesChanged()"
                  />
                }
                <div class="kn-attachments space-y-2">
                  <app-attachment-list
                    #historyList
                    module="knowledge_notes"
                    title="Document history"
                    emptyText="Images and files used in this section."
                    [entityId]="sec.id"
                    [allowUpload]="false"
                    [enablePreview]="true"
                    (removed)="onDocumentRemoved($event)"
                  />
                  <app-attachment-list
                    module="knowledge_notes_extra"
                    title="Additional documents"
                    emptyText="PDFs and extras for this section — not inserted into the note."
                    [entityId]="sec.id"
                  />
                </div>
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
  `,
})
export class KnowledgeSubjectComponent implements OnInit, AfterViewChecked {
  private readonly service = inject(KnowledgeNotesService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly destroyRef = inject(DestroyRef);
  private readonly confirm = inject(ConfirmService);

  @ViewChild('layout') layoutRef?: ElementRef<HTMLElement>;
  @ViewChild('renameInput') renameInput?: ElementRef<HTMLInputElement>;
  @ViewChild(KnowledgeNotesEditorComponent) editor?: KnowledgeNotesEditorComponent;
  @ViewChild('historyList') historyList?: AttachmentListComponent;

  readonly subject = signal<KnowledgeSubjectDetail | null>(null);
  readonly selected = signal<KnowledgeSection | null>(null);
  readonly loading = signal(false);
  readonly previewOnly = signal(false);
  readonly syncState = signal<SyncState>('synced');
  readonly renaming = signal<RenameTarget | null>(null);
  readonly openMenu = signal<string | null>(null);
  readonly resizing = signal(false);
  readonly sidebarWidth = signal(KnowledgeSubjectComponent.readSidebarWidth());
  readonly sectionListIds = computed(() =>
    (this.subject()?.chapters ?? []).map((c) => this.sectionListId(c.id))
  );
  readonly archivedSections = computed(() => this.subject()?.archived_sections ?? []);
  readonly searchQuery = signal('');
  readonly searchHits = signal<KnowledgeSearchHit[]>([]);
  readonly searchOpen = signal(false);
  readonly searchLoaded = signal(false);
  readonly groupedSearchHits = computed<SearchGroup[]>(() => {
    const hits = this.searchHits();
    const groups = new Map<string, SearchGroup>();
    for (const hit of hits) {
      const existing = groups.get(hit.chapter_id);
      if (existing) {
        existing.sections.push(hit);
      } else {
        groups.set(hit.chapter_id, {
          chapter_id: hit.chapter_id,
          chapter_title: hit.chapter_title,
          sections: [hit],
        });
      }
    }
    return Array.from(groups.values());
  });
  readonly noConnectedLists: string[] = [];
  private focusRename = false;
  private expandedChapterIds = new Set<string>();
  private lastSectionByChapter: Record<string, string> = {};
  private lastEditedSectionId: string | null = null;
  private newlyCreatedSectionIds = new Set<string>();
  private searchTimer?: ReturnType<typeof setTimeout>;

  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    content: [''],
  });

  private pendingSectionId: string | null = null;
  private lastSavedTitle = '';
  private lastSavedContent = '';
  private suppressDirty = false;
  private readonly dirty$ = new Subject<void>();

  @HostListener('document:click')
  onDocumentClick(): void {
    this.closeMenu();
    this.closeSearch();
  }

  ngOnInit(): void {
    this.pendingSectionId = this.route.snapshot.queryParamMap.get('section');
    const id = this.route.snapshot.paramMap.get('id');
    if (id) this.load(id);

    this.dirty$
      .pipe(debounceTime(1500), takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.saveIfDirty());

    this.form.controls.title.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        if (this.suppressDirty) return;
        this.refreshSync();
        this.scheduleSave();
      });
  }

  toggleMenu(id: string, event: Event): void {
    event.stopPropagation();
    this.openMenu.update((current) => (current === id ? null : id));
  }

  closeMenu(): void {
    this.openMenu.set(null);
  }

  ngAfterViewChecked(): void {
    if (!this.focusRename) return;
    const el = this.renameInput?.nativeElement;
    if (!el) return;
    this.focusRename = false;
    el.focus({ preventScroll: true });
    el.select();
  }

  archiveDaysLeft(sec: KnowledgeSection): number {
    if (!sec.archived_at) return ARCHIVE_TTL_DAYS;
    const expires = new Date(sec.archived_at).getTime() + ARCHIVE_TTL_DAYS * 24 * 60 * 60 * 1000;
    return Math.max(0, Math.ceil((expires - Date.now()) / (24 * 60 * 60 * 1000)));
  }

  sectionListId(chapterId: string): string {
    return `kn-sec-${chapterId}`;
  }

  private load(id: string): void {
    this.loading.set(true);
    this.selected.set(null);
    this.loadExpandedState(id);
    this.loadLastSections(id);
    this.loadLastEdited(id);
    this.service.getSubject(id).subscribe({
      next: (s) => {
        this.subject.set(s);
        this.loading.set(false);
        this.initExpandedDefaults(s);
        this.restoreSelection();
      },
      error: () => this.loading.set(false),
    });
  }

  private restoreSelection(): void {
    const s = this.subject();
    if (!s) return;
    const all = s.chapters.flatMap((c) => c.sections);
    let target =
      (this.pendingSectionId && all.find((sec) => sec.id === this.pendingSectionId)) ||
      (this.selected() && all.find((sec) => sec.id === this.selected()!.id)) ||
      null;

    if (!target) {
      const resolved = resolveDefaultSection(s, this.lastEditedSectionId);
      target = resolved?.section ?? null;
    }

    this.pendingSectionId = null;
    if (target) {
      const chapter = s.chapters.find((c) => c.sections.some((sec) => sec.id === target!.id));
      if (chapter) this.expandChapter(chapter.id);
      this.selectSection(target, chapter);
    } else {
      this.selected.set(null);
    }
  }

  chapterStatus(chapter: KnowledgeChapter): 'done' | 'ongoing' | null {
    if (chapter.sections.length === 0) return null;
    return isChapterComplete(chapter) ? 'done' : 'ongoing';
  }

  sectionStatus(chapter: KnowledgeChapter, sec: KnowledgeSection): 'done' | 'ongoing' {
    return isSectionComplete(chapter, sec) ? 'done' : 'ongoing';
  }

  selectSection(sec: KnowledgeSection, chapter?: KnowledgeChapter): void {
    const s = this.subject();
    const parent =
      chapter ?? s?.chapters.find((c) => c.sections.some((item) => item.id === sec.id));
    if (parent) {
      this.expandChapter(parent.id);
      this.rememberSection(parent.id, sec.id);
    }

    this.suppressDirty = true;
    this.selected.set(sec);
    this.previewOnly.set(!this.shouldOpenInEditMode(sec, parent));
    this.form.reset({ title: sec.title, content: sec.content });
    this.lastSavedTitle = sec.title;
    this.lastSavedContent = sec.content;
    this.syncState.set('synced');
    this.suppressDirty = false;
  }

  enterEditMode(): void {
    this.previewOnly.set(false);
  }

  cancelEdit(): void {
    const sec = this.selected();
    if (!sec) return;
    this.suppressDirty = true;
    this.form.reset({ title: this.lastSavedTitle, content: this.lastSavedContent });
    sec.title = this.lastSavedTitle;
    sec.content = this.lastSavedContent;
    this.syncState.set('synced');
    this.suppressDirty = false;
    this.previewOnly.set(true);
  }

  private shouldOpenInEditMode(sec: KnowledgeSection, chapter?: KnowledgeChapter): boolean {
    if (this.newlyCreatedSectionIds.has(sec.id)) return true;
    if (sec.closed_at || chapter?.closed_at) return false;
    return false;
  }

  isExpanded(chapterId: string): boolean {
    return this.expandedChapterIds.has(chapterId);
  }

  toggleChapter(chapter: KnowledgeChapter, event: Event): void {
    event.stopPropagation();
    if (this.isExpanded(chapter.id)) {
      this.expandedChapterIds.delete(chapter.id);
    } else {
      this.expandChapter(chapter.id);
      const sec = this.resolveSectionForChapter(chapter);
      if (sec) this.selectSection(sec, chapter);
    }
    this.persistExpandedState();
  }

  onChapterClick(chapter: KnowledgeChapter, event: Event): void {
    event.stopPropagation();
    if (!this.isExpanded(chapter.id)) {
      this.expandChapter(chapter.id);
      const sec = this.resolveSectionForChapter(chapter);
      if (sec) this.selectSection(sec, chapter);
      this.persistExpandedState();
      return;
    }
    this.toggleChapter(chapter, event);
  }

  private expandChapter(chapterId: string): void {
    this.expandedChapterIds.add(chapterId);
  }

  private initExpandedDefaults(subject: KnowledgeSubjectDetail): void {
    if (this.expandedChapterIds.size > 0) return;
    const selectedId =
      this.pendingSectionId ??
      this.selected()?.id ??
      resolveDefaultSection(subject, this.lastEditedSectionId)?.section.id;
    if (selectedId) {
      const chapter = subject.chapters.find((c) => c.sections.some((s) => s.id === selectedId));
      if (chapter) {
        this.expandChapter(chapter.id);
        return;
      }
    }
    if (subject.chapters[0]) {
      this.expandChapter(subject.chapters[0].id);
    }
  }

  private resolveSectionForChapter(chapter: KnowledgeChapter): KnowledgeSection | undefined {
    const remembered = this.lastSectionByChapter[chapter.id];
    if (remembered) {
      const match = chapter.sections.find((s) => s.id === remembered);
      if (match) return match;
    }
    return chapter.sections[0];
  }

  private rememberSection(chapterId: string, sectionId: string): void {
    this.lastSectionByChapter[chapterId] = sectionId;
    this.persistLastSections();
    this.rememberLastEdited(sectionId);
  }

  private rememberLastEdited(sectionId: string): void {
    this.lastEditedSectionId = sectionId;
    this.persistLastEdited();
  }

  private loadLastEdited(subjectId: string): void {
    this.lastEditedSectionId = localStorage.getItem(LAST_EDITED_PREFIX + subjectId);
  }

  private persistLastEdited(): void {
    const subjectId = this.subject()?.id;
    if (!subjectId || !this.lastEditedSectionId) return;
    localStorage.setItem(LAST_EDITED_PREFIX + subjectId, this.lastEditedSectionId);
  }

  private loadExpandedState(subjectId: string): void {
    try {
      const raw = localStorage.getItem(EXPANDED_PREFIX + subjectId);
      this.expandedChapterIds = new Set(raw ? (JSON.parse(raw) as string[]) : []);
    } catch {
      this.expandedChapterIds = new Set();
    }
  }

  private persistExpandedState(): void {
    const subjectId = this.subject()?.id;
    if (!subjectId) return;
    localStorage.setItem(
      EXPANDED_PREFIX + subjectId,
      JSON.stringify(Array.from(this.expandedChapterIds))
    );
  }

  private loadLastSections(subjectId: string): void {
    try {
      const raw = localStorage.getItem(LAST_SECTION_PREFIX + subjectId);
      this.lastSectionByChapter = raw ? (JSON.parse(raw) as Record<string, string>) : {};
    } catch {
      this.lastSectionByChapter = {};
    }
  }

  private persistLastSections(): void {
    const subjectId = this.subject()?.id;
    if (!subjectId) return;
    localStorage.setItem(LAST_SECTION_PREFIX + subjectId, JSON.stringify(this.lastSectionByChapter));
  }

  onSearchInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.searchQuery.set(value);
    this.searchOpen.set(true);
    this.searchLoaded.set(false);
    clearTimeout(this.searchTimer);
    const q = value.trim();
    if (!q) {
      this.searchHits.set([]);
      this.searchLoaded.set(true);
      return;
    }
    const subjectId = this.subject()?.id;
    if (!subjectId) return;
    this.searchTimer = setTimeout(() => {
      this.service.search(q, subjectId).subscribe({
        next: (hits) => {
          this.searchHits.set(hits);
          this.searchLoaded.set(true);
        },
        error: () => {
          this.searchHits.set([]);
          this.searchLoaded.set(true);
        },
      });
    }, 300);
  }

  closeSearch(): void {
    this.searchOpen.set(false);
  }

  openSearchHit(hit: KnowledgeSearchHit): void {
    const s = this.subject();
    if (!s) return;
    const chapter = s.chapters.find((c) => c.id === hit.chapter_id);
    const section = chapter?.sections.find((sec) => sec.id === hit.section_id);
    if (!chapter || !section) return;
    this.expandChapter(chapter.id);
    this.persistExpandedState();
    this.selectSection(section, chapter);
    this.closeSearch();
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { section: section.id },
      queryParamsHandling: 'merge',
    });
  }

  toggleSectionClosed(sec: KnowledgeSection, closed: boolean): void {
    this.service.updateSection(sec.id, { closed }).subscribe({
      next: (updated) => {
        sec.closed_at = updated.closed_at ?? null;
        this.patchSection({ ...sec, closed_at: updated.closed_at ?? null });
        if (closed && this.selected()?.id === sec.id) {
          this.previewOnly.set(true);
        }
      },
    });
  }

  toggleChapterClosed(chapter: KnowledgeChapter, closed: boolean): void {
    this.service.updateChapter(chapter.id, { closed }).subscribe({
      next: (updated) => {
        chapter.closed_at = updated.closed_at ?? null;
        this.subject.set({ ...this.subject()!, chapters: [...this.subject()!.chapters] });
        if (closed && this.selected()) {
          const selectedChapter = this.subject()?.chapters.find((c) =>
            c.sections.some((s) => s.id === this.selected()!.id)
          );
          if (selectedChapter?.id === chapter.id) {
            this.previewOnly.set(true);
          }
        }
      },
    });
  }

  onEditorContentChange(content: string): void {
    this.form.controls.content.setValue(content, { emitEvent: false });
    const sec = this.selected();
    if (sec) sec.content = content;
    if (this.suppressDirty) return;
    this.refreshSync();
    this.scheduleSave();
  }

  onEditorReady(): void {
    if (this.renaming()) this.queueRenameFocus();
  }

  onEditorSaved(updated: KnowledgeSection): void {
    this.lastSavedContent = updated.content;
    this.patchSection(updated);
    this.refreshSync();
  }

  onInlineFilesChanged(): void {
    this.historyList?.load();
  }

  onDocumentRemoved(file: FileRecord): void {
    const next = stripFileMarkdown(this.form.controls.content.value, file.id);
    if (next === this.form.controls.content.value) return;
    this.form.controls.content.setValue(next, { emitEvent: false });
    const sec = this.selected();
    if (sec) sec.content = next;
    this.editor?.setContent(next);
    this.refreshSync();
    this.saveIfDirty();
  }

  save(): void {
    this.saveIfDirty(true);
  }

  private scheduleSave(): void {
    if (this.syncState() === 'unsaved') this.dirty$.next();
  }

  private saveIfDirty(returnToRead = false): void {
    const sec = this.selected();
    if (!sec || this.form.invalid || this.syncState() === 'saving') return;
    const raw = this.form.getRawValue();
    if (raw.title === this.lastSavedTitle && raw.content === this.lastSavedContent) {
      this.syncState.set('synced');
      return;
    }
    const wasNew = this.newlyCreatedSectionIds.has(sec.id);
    this.syncState.set('saving');
    this.service.updateSection(sec.id, { title: raw.title, content: raw.content }).subscribe({
      next: (updated) => {
        this.lastSavedTitle = raw.title;
        this.lastSavedContent = raw.content;
        this.patchSection({ ...updated, title: raw.title, content: raw.content });
        const current = this.form.getRawValue();
        if (current.title !== raw.title || current.content !== raw.content) {
          this.syncState.set('unsaved');
          this.scheduleSave();
        } else {
          this.syncState.set('synced');
          if (returnToRead) {
            if (wasNew) {
              this.newlyCreatedSectionIds.delete(sec.id);
            }
            this.previewOnly.set(true);
          }
        }
      },
      error: () => this.syncState.set('unsaved'),
    });
  }

  private refreshSync(): void {
    if (this.syncState() === 'saving') return;
    const raw = this.form.getRawValue();
    this.syncState.set(
      raw.title === this.lastSavedTitle && raw.content === this.lastSavedContent ? 'synced' : 'unsaved'
    );
  }

  patchSection(updated: KnowledgeSection): void {
    const s = this.subject();
    if (!s) return;
    for (const c of s.chapters) {
      const idx = c.sections.findIndex((x) => x.id === updated.id);
      if (idx !== -1) c.sections[idx] = { ...c.sections[idx], ...updated };
    }
    this.subject.set({ ...s });
    if (this.selected()?.id === updated.id) {
      this.selected.set({ ...this.selected()!, ...updated });
    }
  }

  addChapter(): void {
    const s = this.subject();
    if (!s) return;
    this.service.createChapter(s.id, { title: 'Untitled' }).subscribe({
      next: (chapter) => {
        chapter.sections = chapter.sections ?? [];
        s.chapters = [...s.chapters, chapter];
        this.subject.set({ ...s });
        this.startRename('chapter', chapter.id);
      },
    });
  }

  addSection(chapter: KnowledgeChapter): void {
    this.service.createSection(chapter.id, { title: 'Untitled', content: '' }).subscribe({
      next: (sec) => {
        chapter.sections = [...chapter.sections, sec];
        this.subject.set({ ...this.subject()! });
        this.expandChapter(chapter.id);
        this.persistExpandedState();
        this.newlyCreatedSectionIds.add(sec.id);
        sec.content = '';
        this.selectSection(sec, chapter);
        this.startRename('section', sec.id);
      },
    });
  }

  startRename(kind: RenameTarget['kind'], id: string, event?: Event): void {
    event?.preventDefault();
    event?.stopPropagation();
    this.closeMenu();
    this.renaming.set({ kind, id });
    this.queueRenameFocus();
  }

  private queueRenameFocus(): void {
    this.focusRename = true;
    setTimeout(() => {
      this.renameInput?.nativeElement.focus({ preventScroll: true });
      this.renameInput?.nativeElement.select();
    }, 0);
    setTimeout(() => {
      this.renameInput?.nativeElement.focus({ preventScroll: true });
      this.renameInput?.nativeElement.select();
    }, 80);
  }

  cancelRename(): void {
    this.renaming.set(null);
  }

  commitRename(event: Event): void {
    const target = this.renaming();
    const input = event.target as HTMLInputElement | null;
    const value = (input?.value ?? '').trim();
    this.renaming.set(null);
    if (!target) return;
    if (!value) return;

    if (target.kind === 'subject') {
      const s = this.subject();
      if (!s || value === s.title) return;
      this.service.updateSubject(s.id, { title: value }).subscribe({
        next: () => {
          this.subject.set({ ...s, title: value });
        },
      });
      return;
    }
    if (target.kind === 'chapter') {
      const s = this.subject();
      const chapter = s?.chapters.find((c) => c.id === target.id);
      if (!chapter || value === chapter.title) return;
      this.service.updateChapter(target.id, { title: value }).subscribe({
        next: () => {
          chapter.title = value;
          this.subject.set({ ...s! });
        },
      });
      return;
    }
    const s = this.subject();
    const section = s?.chapters.flatMap((c) => c.sections).find((sec) => sec.id === target.id);
    if (!section || value === section.title) return;
    this.service.updateSection(target.id, { title: value }).subscribe({
      next: () => {
        section.title = value;
        if (this.selected()?.id === section.id) {
          this.suppressDirty = true;
          this.form.controls.title.setValue(value);
          this.lastSavedTitle = value;
          this.suppressDirty = false;
          this.refreshSync();
        }
        this.subject.set({ ...s! });
      },
    });
  }

  onChapterDrop(event: CdkDragDrop<KnowledgeChapter[]>): void {
    if (event.previousIndex === event.currentIndex) return;
    moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
    const s = this.subject();
    if (!s) return;
    this.subject.set({ ...s, chapters: [...event.container.data] });
    const reqs = event.container.data.map((c, i) => {
      c.order_index = i;
      return this.service.updateChapter(c.id, { order_index: i });
    });
    if (reqs.length) forkJoin(reqs).subscribe();
  }

  onSectionDrop(event: CdkDragDrop<KnowledgeSection[]>): void {
    if (event.previousContainer === event.container && event.previousIndex === event.currentIndex) {
      return;
    }
    if (event.previousContainer === event.container) {
      moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
    } else {
      transferArrayItem(
        event.previousContainer.data,
        event.container.data,
        event.previousIndex,
        event.currentIndex
      );
    }
    const targetChapterId = event.container.id.replace('kn-sec-', '');
    const persist: KnowledgeSection[] = [];
    event.container.data.forEach((sec, i) => {
      sec.chapter_id = targetChapterId;
      sec.order_index = i;
      persist.push(sec);
    });
    if (event.previousContainer !== event.container) {
      event.previousContainer.data.forEach((sec, i) => {
        sec.order_index = i;
        persist.push(sec);
      });
    }
    const s = this.subject();
    if (s) this.subject.set({ ...s, chapters: s.chapters.map((c) => ({ ...c, sections: [...c.sections] })) });
    const selected = this.selected();
    if (selected) {
      const moved = persist.find((sec) => sec.id === selected.id);
      if (moved) this.selected.set({ ...selected, chapter_id: moved.chapter_id });
    }
    const reqs = persist.map((sec) =>
      this.service.updateSection(sec.id, { order_index: sec.order_index, chapter_id: sec.chapter_id })
    );
    if (reqs.length) forkJoin(reqs).subscribe();
  }

  async deleteSection(sec: KnowledgeSection): Promise<void> {
    const ok = await this.confirm.confirm(
      `Delete “${sec.title}”? It moves to Archived and is permanently removed after ${ARCHIVE_TTL_DAYS} days.`,
      'Delete section'
    );
    if (!ok) return;
    this.service.archiveSection(sec.id).subscribe({
      next: (updated) => {
        const s = this.subject();
        if (!s) return;
        for (const chapter of s.chapters) {
          chapter.sections = chapter.sections.filter((item) => item.id !== sec.id);
        }
        s.archived_sections = [...(s.archived_sections ?? []), { ...sec, ...updated }];
        this.subject.set({ ...s, chapters: s.chapters.map((c) => ({ ...c, sections: [...c.sections] })) });
        if (this.selected()?.id === sec.id) this.restoreSelection();
      },
    });
  }

  async deletePermanently(sec: KnowledgeSection): Promise<void> {
    const ok = await this.confirm.confirm(
      `Permanently delete “${sec.title}”? This cannot be undone.`,
      'Delete section'
    );
    if (!ok) return;
    this.service.deleteSection(sec.id).subscribe({ next: () => this.reload() });
  }

  restoreSection(sec: KnowledgeSection): void {
    this.service.restoreSection(sec.id).subscribe({
      next: (updated) => {
        const s = this.subject();
        if (!s) return;
        s.archived_sections = (s.archived_sections ?? []).filter((item) => item.id !== sec.id);
        const chapter = s.chapters.find((c) => c.id === updated.chapter_id) ?? s.chapters.find((c) => c.id === sec.chapter_id);
        if (chapter) {
          chapter.sections = [...chapter.sections, { ...sec, ...updated, archived_at: null }];
        }
        this.subject.set({ ...s, chapters: s.chapters.map((c) => ({ ...c, sections: [...c.sections] })) });
      },
    });
  }

  async deleteChapter(c: KnowledgeChapter): Promise<void> {
    const ok = await this.confirm.confirm(
      `Delete chapter “${c.title}” and all its sections?`,
      'Delete chapter'
    );
    if (!ok) return;
    this.service.deleteChapter(c.id).subscribe({ next: () => this.reload() });
  }

  async deleteSubject(): Promise<void> {
    const s = this.subject();
    if (!s) return;
    const ok = await this.confirm.confirm(
      `Delete subject “${s.title}” and everything in it?`,
      'Delete subject'
    );
    if (!ok) return;
    this.service.deleteSubject(s.id).subscribe({ next: () => this.router.navigate(['/knowledge']) });
  }

  onResizePointerDown(event: PointerEvent): void {
    if (event.button !== 0) return;
    event.preventDefault();
    this.resizing.set(true);
    (event.target as HTMLElement).setPointerCapture(event.pointerId);
  }

  onResizePointerMove(event: PointerEvent): void {
    if (!this.resizing()) return;
    const rect = this.layoutRef?.nativeElement.getBoundingClientRect();
    if (!rect) return;
    const width = Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, event.clientX - rect.left));
    this.sidebarWidth.set(width);
  }

  onResizePointerUp(event: PointerEvent): void {
    if (!this.resizing()) return;
    this.resizing.set(false);
    try {
      (event.target as HTMLElement).releasePointerCapture(event.pointerId);
    } catch {
      /* already released */
    }
    localStorage.setItem(SIDEBAR_KEY, String(this.sidebarWidth()));
  }

  resetSidebarWidth(): void {
    this.sidebarWidth.set(SIDEBAR_DEFAULT);
    localStorage.setItem(SIDEBAR_KEY, String(SIDEBAR_DEFAULT));
  }

  onResizeKeydown(event: KeyboardEvent): void {
    const step = event.shiftKey ? 32 : 16;
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      this.sidebarWidth.update((w) => Math.max(SIDEBAR_MIN, w - step));
      localStorage.setItem(SIDEBAR_KEY, String(this.sidebarWidth()));
    } else if (event.key === 'ArrowRight') {
      event.preventDefault();
      this.sidebarWidth.update((w) => Math.min(SIDEBAR_MAX, w + step));
      localStorage.setItem(SIDEBAR_KEY, String(this.sidebarWidth()));
    }
  }

  private reload(): void {
    const s = this.subject();
    if (s) this.load(s.id);
  }

  private static readSidebarWidth(): number {
    const raw = Number(localStorage.getItem(SIDEBAR_KEY));
    if (!Number.isFinite(raw)) return SIDEBAR_DEFAULT;
    return Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, raw));
  }
}

const ARCHIVE_TTL_DAYS = 7;

export function isSectionComplete(chapter: KnowledgeChapter, sec: KnowledgeSection): boolean {
  return !!(chapter.closed_at || sec.closed_at);
}

export function isChapterComplete(chapter: KnowledgeChapter): boolean {
  if (chapter.closed_at) return true;
  return chapter.sections.length > 0 && chapter.sections.every((s) => !!s.closed_at);
}

export function resolveDefaultSection(
  subject: KnowledgeSubjectDetail,
  lastEditedSectionId: string | null
): { section: KnowledgeSection; chapter: KnowledgeChapter } | null {
  const pairs: { section: KnowledgeSection; chapter: KnowledgeChapter }[] = [];
  for (const chapter of subject.chapters) {
    for (const section of chapter.sections) {
      pairs.push({ section, chapter });
    }
  }
  if (pairs.length === 0) return null;

  const incomplete = pairs.filter(({ section, chapter }) => !isSectionComplete(chapter, section));

  if (incomplete.length === 0) {
    return pairs[0];
  }

  if (lastEditedSectionId) {
    const lastEdited = incomplete.find(({ section }) => section.id === lastEditedSectionId);
    if (lastEdited) return lastEdited;
  }

  return incomplete[0];
}

export function stripFileMarkdown(content: string, fileId: string): string {
  if (!content || !fileId) return content;
  const escaped = fileId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp(`!?\\[[^\\]]*\\]\\([^)]*\\/files\\/${escaped}\\/content[^)]*\\)`, 'gi');
  return content.replace(re, '').replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trimEnd();
}
