import {
  CdkDragDrop,
  moveItemInArray,
  transferArrayItem,
} from '@angular/cdk/drag-drop';
import { Component, DestroyRef, ElementRef, HostListener, AfterViewChecked, OnInit, ViewChild, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Subject, forkJoin } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { ConfirmService } from '../../shared/confirm/confirm.service';
import { MarkdownImportResult } from '../../shared/markdown/markdown-import.service';
import { downloadMarkdown } from '../../shared/markdown/markdown-export';
import { FileRecord } from '../files/models/file.models';
import { IntegrationsService, GitHubSectionSyncDisplay } from '../integrations/services/integrations.service';
import { ModalComponent } from '../../shared/modal/modal.component';
import { KnowledgeSectionEditorComponent } from './components/knowledge-section-editor.component';
import { KnowledgeChapterDocumentsComponent } from './components/knowledge-chapter-documents.component';
import { KnowledgeRenameTarget, KnowledgeSidebarComponent } from './components/knowledge-sidebar.component';
import {
  KnowledgeChapter,
  KnowledgeChapterDocument,
  KnowledgeChapterDocumentsGroup,
  KnowledgeSearchHit,
  KnowledgeSection,
  KnowledgeSubjectDetail,
} from './models/knowledge-notes.models';
import { KnowledgeNotesService } from './services/knowledge-notes.service';
import {
  resolveDefaultSection,
  stripFileMarkdown,
} from './knowledge-notes.utils';
import {
  SIDEBAR_DEFAULT,
  SIDEBAR_MAX,
  SIDEBAR_MIN,
  readExpandedChapters,
  readLastEdited,
  readLastSections,
  readSidebarWidth,
  writeExpandedChapters,
  writeLastEdited,
  writeLastSections,
  writeSidebarWidth,
} from './knowledge-subject-view-state';

type SyncState = 'synced' | 'unsaved' | 'saving';
type RenameTarget = KnowledgeRenameTarget;
type SearchGroup = { chapter_id: string; chapter_title: string; sections: KnowledgeSearchHit[] };

const ARCHIVE_TTL_DAYS = 7;

@Component({
  selector: 'app-knowledge-subject',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    ModalComponent,
    KnowledgeSidebarComponent,
    KnowledgeSectionEditorComponent,
    KnowledgeChapterDocumentsComponent,
  ],
  template: `
    @if (subject(); as s) {
      <div class="space-y-2">
        <div class="kn-breadcrumb">
          <nav class="kn-breadcrumb__nav" aria-label="Notes">
            <a routerLink="/knowledge" class="kn-breadcrumb__link">← Notes</a>
            <span class="kn-breadcrumb__sep" aria-hidden="true">/</span>
            <span
              class="text-lg leading-none shrink-0"
              title="Double-click to edit icon"
              (dblclick)="openSubjectDetails($event)"
            >{{ s.icon || '📘' }}</span>
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
                <button type="button" class="menu-item" role="menuitem" (click)="openSubjectDetails(); closeMenu()">Edit details</button>
                <button type="button" class="menu-item" role="menuitem" (click)="openDocuments(); closeMenu()">Documents</button>
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
          <app-knowledge-sidebar
            [subject]="s"
            [selected]="selected()"
            [renaming]="renaming()"
            [openMenu]="openMenu()"
            [expandedChapterIds]="expandedChapterIds"
            [sectionListIds]="sectionListIds()"
            [archivedSections]="archivedSections()"
            [noConnectedLists]="noConnectedLists"
            [githubConfigured]="githubConfigured()"
            [sectionSyncStatuses]="sectionSyncStatuses()"
            [syncState]="syncState()"
            (addChapter)="addChapter()"
            (chapterDrop)="onChapterDrop($event)"
            (sectionDrop)="onSectionDrop($event)"
            (toggleChapter)="toggleChapter($event.chapter, $event.event)"
            (chapterClick)="onChapterClick($event.chapter, $event.event)"
            (startRename)="startRename($event.kind, $event.id, $event.event)"
            (commitRename)="commitRename($event)"
            (cancelRename)="cancelRename()"
            (addSection)="addSection($event)"
            (toggleMenu)="toggleMenu($event.id, $event.event)"
            (closeMenu)="closeMenu()"
            (toggleChapterClosed)="toggleChapterClosed($event.chapter, $event.closed)"
            (deleteChapter)="deleteChapter($event)"
            (openChapterDocuments)="openDocuments($event.id)"
            (selectSection)="selectSection($event.section, $event.chapter)"
            (deleteSection)="deleteSection($event)"
            (restoreSection)="restoreSection($event)"
            (deletePermanently)="deletePermanently($event)"
          />

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

          @if (documentsOpen()) {
            <app-knowledge-chapter-documents
              [groups]="documentGroups()"
              [loading]="documentsLoading()"
              [error]="documentsError()"
              [chapterFilter]="documentsChapterId()"
              (removed)="onChapterDocumentRemoved($event)"
              (showAll)="openDocuments()"
              (closed)="closeDocuments()"
              (openSection)="openDocumentSection($event.sectionId, $event.chapterId)"
            />
          } @else {
          <app-knowledge-section-editor
            [section]="selected()"
            [form]="form"
            [previewOnly]="previewOnly()"
            [syncState]="syncState()"
            [importError]="importError()"
            [githubConfigured]="githubConfigured()"
            [githubMessage]="githubMessage()"
            [githubMessageSectionId]="githubMessageSectionId()"
            [sectionSyncStatuses]="sectionSyncStatuses()"
            [openMenu]="openMenu()"
            [beforeSync]="saveBeforeGitHubSyncBound"
            (markdownImported)="onMarkdownImported($event)"
            (markdownImportError)="onMarkdownImportError($event)"
            (gitHubSyncSuccess)="onGitHubSyncSuccess($event.message, $event.sectionId)"
            (gitHubSyncError)="onGitHubSyncError($event)"
            (enterEditMode)="enterEditMode()"
            (save)="save()"
            (cancelEdit)="cancelEdit()"
            (toggleMenu)="toggleMenu($event.id, $event.event)"
            (closeMenu)="closeMenu()"
            (exportSectionMarkdown)="exportSectionMarkdown()"
            (toggleSectionClosed)="toggleSectionClosed($event.section, $event.closed)"
            (deleteSection)="deleteSection($event)"
            (editorContentChange)="onEditorContentChange($event)"
            (editorSaved)="onEditorSaved($event)"
            (editorReady)="onEditorReady()"
            (inlineFilesChanged)="onInlineFilesChanged()"
            (documentRemoved)="onDocumentRemoved($event)"
          />
          }
        </div>
      </div>

      <app-modal [open]="detailsOpen()" title="Edit subject" (closed)="detailsOpen.set(false)">
        <form [formGroup]="subjectDetailsForm" class="space-y-3 text-sm" body (ngSubmit)="saveSubjectDetails()">
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
          <button type="button" class="btn-secondary text-xs" (click)="detailsOpen.set(false)">Cancel</button>
          <button type="button" class="btn-primary text-xs" [disabled]="savingDetails()" (click)="saveSubjectDetails()">
            {{ savingDetails() ? 'Saving…' : 'Save' }}
          </button>
        </div>
      </app-modal>
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
  private readonly integrations = inject(IntegrationsService);

  @ViewChild('layout') layoutRef?: ElementRef<HTMLElement>;
  @ViewChild('renameInput') renameInput?: ElementRef<HTMLInputElement>;
  @ViewChild(KnowledgeSidebarComponent) sidebar?: KnowledgeSidebarComponent;
  @ViewChild(KnowledgeSectionEditorComponent) sectionEditor?: KnowledgeSectionEditorComponent;

  readonly subject = signal<KnowledgeSubjectDetail | null>(null);
  readonly selected = signal<KnowledgeSection | null>(null);
  readonly loading = signal(false);
  readonly previewOnly = signal(false);
  readonly syncState = signal<SyncState>('synced');
  readonly importError = signal('');
  readonly githubConfigured = signal(false);
  readonly githubMessage = signal<string | null>(null);
  readonly githubMessageSectionId = signal<string | null>(null);
  readonly sectionSyncStatuses = signal<Record<string, GitHubSectionSyncDisplay>>({});
  readonly renaming = signal<RenameTarget | null>(null);
  readonly openMenu = signal<string | null>(null);
  readonly detailsOpen = signal(false);
  readonly savingDetails = signal(false);
  readonly resizing = signal(false);
  readonly sidebarWidth = signal(readSidebarWidth());
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
  readonly documentsOpen = signal(false);
  readonly documentsChapterId = signal<string | null>(null);
  readonly documentGroups = signal<KnowledgeChapterDocumentsGroup[]>([]);
  readonly documentsLoading = signal(false);
  readonly documentsError = signal('');
  readonly noConnectedLists: string[] = [];
  private focusRename = false;
  expandedChapterIds = new Set<string>();
  private lastSectionByChapter: Record<string, string> = {};
  private lastEditedSectionId: string | null = null;
  private newlyCreatedSectionIds = new Set<string>();
  private searchTimer?: ReturnType<typeof setTimeout>;

  form = this.fb.nonNullable.group({
    title: ['', Validators.required],
    content: [''],
  });

  subjectDetailsForm = this.fb.nonNullable.group({
    icon: [''],
    description: [''],
  });

  private pendingSectionId: string | null = null;
  private lastSavedTitle = '';
  private lastSavedContent = '';
  private suppressDirty = false;
  private readonly dirty$ = new Subject<void>();
  readonly saveBeforeGitHubSyncBound = () => this.saveBeforeGitHubSync();

  @HostListener('document:click')
  onDocumentClick(): void {
    this.closeMenu();
    this.closeSearch();
  }

  ngOnInit(): void {
    this.pendingSectionId = this.route.snapshot.queryParamMap.get('section');
    const id = this.route.snapshot.paramMap.get('id');
    if (id) this.load(id);

    this.integrations.getGitHub().subscribe({
      next: (status) => {
        const configured = !!(status.configured && status.enabled);
        this.githubConfigured.set(configured);
        if (configured && this.subject()?.id) {
          this.reloadGitHubSyncStatuses(this.subject()!.id);
        } else if (!configured) {
          this.sectionSyncStatuses.set({});
        }
      },
      error: () => {
        this.githubConfigured.set(false);
        this.sectionSyncStatuses.set({});
      },
    });

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
    const kind = this.renaming()?.kind;
    if (kind === 'chapter' || kind === 'section') {
      const el = this.sidebar?.renameInput?.nativeElement;
      if (!el) return;
      this.focusRename = false;
      el.focus({ preventScroll: true });
      el.select();
      return;
    }
    const el = this.renameInput?.nativeElement;
    if (!el) return;
    this.focusRename = false;
    el.focus({ preventScroll: true });
    el.select();
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
        this.reloadGitHubSyncStatuses(id);
        if (this.documentsOpen()) {
          const filter = this.documentsChapterId();
          if (filter && !s.chapters.some((c) => c.id === filter)) {
            this.documentsChapterId.set(null);
          }
          this.loadDocuments();
        }
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
      this.applySectionSelection(target, chapter);
    } else {
      this.selected.set(null);
    }
  }

  selectSection(sec: KnowledgeSection, chapter?: KnowledgeChapter): void {
    this.documentsOpen.set(false);
    this.applySectionSelection(sec, chapter);
  }

  private applySectionSelection(sec: KnowledgeSection, chapter?: KnowledgeChapter): void {
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
    this.importError.set('');
    this.githubMessage.set(null);
    this.githubMessageSectionId.set(null);
    this.suppressDirty = false;
  }

  enterEditMode(): void {
    this.previewOnly.set(false);
  }

  onMarkdownImported(result: MarkdownImportResult): void {
    const sec = this.selected();
    if (!sec) return;
    this.importError.set('');

    if (result.title) {
      this.form.controls.title.setValue(result.title, { emitEvent: false });
      sec.title = result.title;
    }

    this.form.controls.content.setValue(result.content, { emitEvent: false });
    sec.content = result.content;

    if (this.previewOnly()) {
      this.enterEditMode();
    }

    this.sectionEditor?.setContent(result.content);
    this.refreshSync();
    this.scheduleSave();
  }

  onMarkdownImportError(message: string): void {
    this.importError.set(message);
  }

  onGitHubSyncSuccess(message: string, sectionId: string): void {
    this.importError.set('');
    this.githubMessage.set(message);
    this.githubMessageSectionId.set(sectionId);
    const subjectId = this.subject()?.id;
    if (subjectId) this.reloadGitHubSyncStatuses(subjectId);
  }

  onGitHubSyncError(message: string): void {
    this.githubMessage.set(null);
    this.githubMessageSectionId.set(null);
    this.importError.set(message);
    const subjectId = this.subject()?.id;
    if (subjectId) this.reloadGitHubSyncStatuses(subjectId);
  }

  private reloadGitHubSyncStatuses(subjectId: string): void {
    if (!this.githubConfigured()) {
      this.sectionSyncStatuses.set({});
      return;
    }
    this.integrations.getGitHubSectionSyncStatuses(subjectId).subscribe({
      next: (res) => {
        const map: Record<string, GitHubSectionSyncDisplay> = {};
        for (const item of res.sections) {
          map[item.section_id] = item.status;
        }
        this.sectionSyncStatuses.set(map);
      },
      error: () => this.sectionSyncStatuses.set({}),
    });
  }

  saveBeforeGitHubSync(): Promise<void> {
    const sec = this.selected();
    if (!sec || this.form.invalid) {
      return Promise.reject(new Error('Fix validation errors before syncing'));
    }
    if (this.syncState() === 'saving') {
      return Promise.reject(new Error('Wait for save to finish'));
    }
    const raw = this.form.getRawValue();
    if (raw.title === this.lastSavedTitle && raw.content === this.lastSavedContent) {
      return Promise.resolve();
    }
    return new Promise((resolve, reject) => {
      this.service.updateSection(sec.id, { title: raw.title, content: raw.content }).subscribe({
        next: (updated) => {
          this.lastSavedTitle = raw.title;
          this.lastSavedContent = raw.content;
          this.patchSection({ ...updated, title: raw.title, content: raw.content });
          this.syncState.set('synced');
          resolve();
        },
        error: () => reject(new Error('Save failed — sync aborted')),
      });
    });
  }

  exportSectionMarkdown(): void {
    try {
      downloadMarkdown(
        this.form.controls.content.value,
        this.form.controls.title.value || 'section'
      );
      this.importError.set('');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Export failed.';
      this.importError.set(message);
    }
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
    this.lastEditedSectionId = readLastEdited(subjectId);
  }

  private persistLastEdited(): void {
    const subjectId = this.subject()?.id;
    if (!subjectId || !this.lastEditedSectionId) return;
    writeLastEdited(subjectId, this.lastEditedSectionId);
  }

  private loadExpandedState(subjectId: string): void {
    this.expandedChapterIds = readExpandedChapters(subjectId);
  }

  private persistExpandedState(): void {
    const subjectId = this.subject()?.id;
    if (!subjectId) return;
    writeExpandedChapters(subjectId, this.expandedChapterIds);
  }

  private loadLastSections(subjectId: string): void {
    this.lastSectionByChapter = readLastSections(subjectId);
  }

  private persistLastSections(): void {
    const subjectId = this.subject()?.id;
    if (!subjectId) return;
    writeLastSections(subjectId, this.lastSectionByChapter);
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
    this.sectionEditor?.reloadHistory();
  }

  onDocumentRemoved(file: FileRecord): void {
    const next = stripFileMarkdown(this.form.controls.content.value, file.id);
    if (next === this.form.controls.content.value) return;
    this.form.controls.content.setValue(next, { emitEvent: false });
    const sec = this.selected();
    if (sec) sec.content = next;
    this.sectionEditor?.setContent(next);
    this.refreshSync();
    this.saveIfDirty();
  }

  openDocuments(chapterId?: string): void {
    this.closeMenu();
    this.closeSearch();
    this.documentsOpen.set(true);
    this.documentsChapterId.set(chapterId ?? null);
    this.loadDocuments();
  }

  closeDocuments(): void {
    this.documentsOpen.set(false);
    this.documentsError.set('');
  }

  openDocumentSection(sectionId: string, chapterId: string): void {
    const s = this.subject();
    const chapter = s?.chapters.find((c) => c.id === chapterId);
    const section = chapter?.sections.find((sec) => sec.id === sectionId);
    if (!chapter || !section) return;
    this.selectSection(section, chapter);
  }

  onChapterDocumentRemoved(doc: KnowledgeChapterDocument): void {
    if (doc.module === 'knowledge_notes') {
      if (this.selected()?.id === doc.section_id) {
        this.onDocumentRemoved(doc);
      } else {
        this.stripDocumentFromSection(doc);
      }
    }
    if (this.selected()?.id === doc.section_id) {
      this.sectionEditor?.reloadHistory();
    }
    this.loadDocuments();
  }

  private stripDocumentFromSection(doc: KnowledgeChapterDocument): void {
    const s = this.subject();
    const section = s?.chapters
      .flatMap((c) => c.sections)
      .find((sec) => sec.id === doc.section_id);
    if (!section) return;
    const next = stripFileMarkdown(section.content, doc.id);
    if (next === section.content) return;
    this.service.updateSection(section.id, { title: section.title, content: next }).subscribe({
      next: (updated) => this.patchSection({ ...updated, content: next }),
    });
  }

  private loadDocuments(): void {
    const subjectId = this.subject()?.id;
    if (!subjectId || !this.documentsOpen()) return;
    this.documentsLoading.set(true);
    this.documentsError.set('');
    this.service.listDocuments(subjectId, this.documentsChapterId()).subscribe({
      next: (groups) => {
        this.documentGroups.set(groups);
        this.documentsLoading.set(false);
      },
      error: () => {
        this.documentGroups.set([]);
        this.documentsLoading.set(false);
        this.documentsError.set('Could not load documents.');
      },
    });
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
          const subjectId = this.subject()?.id;
          if (subjectId) this.reloadGitHubSyncStatuses(subjectId);
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
      const el =
        this.renaming()?.kind === 'subject'
          ? this.renameInput?.nativeElement
          : this.sidebar?.renameInput?.nativeElement;
      el?.focus({ preventScroll: true });
      el?.select();
    }, 0);
    setTimeout(() => {
      const el =
        this.renaming()?.kind === 'subject'
          ? this.renameInput?.nativeElement
          : this.sidebar?.renameInput?.nativeElement;
      el?.focus({ preventScroll: true });
      el?.select();
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
        this.reloadGitHubSyncStatuses(s!.id);
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
    if (reqs.length) {
      forkJoin(reqs).subscribe({
        complete: () => this.reloadGitHubSyncStatuses(s!.id),
      });
    }
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
    if (reqs.length) {
      forkJoin(reqs).subscribe({
        complete: () => {
          const subjectId = this.subject()?.id;
          if (subjectId) this.reloadGitHubSyncStatuses(subjectId);
        },
      });
    }
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

  openSubjectDetails(event?: Event): void {
    event?.preventDefault();
    event?.stopPropagation();
    const s = this.subject();
    if (!s) return;
    this.subjectDetailsForm.reset({
      icon: s.icon ?? '',
      description: s.description ?? '',
    });
    this.detailsOpen.set(true);
  }

  saveSubjectDetails(): void {
    const s = this.subject();
    if (!s || this.savingDetails()) return;
    const raw = this.subjectDetailsForm.getRawValue();
    const icon = raw.icon.trim() || null;
    const description = raw.description.trim() || null;
    if (icon === (s.icon ?? null) && description === (s.description ?? null)) {
      this.detailsOpen.set(false);
      return;
    }
    this.savingDetails.set(true);
    this.service.updateSubject(s.id, { icon, description }).subscribe({
      next: () => {
        this.subject.set({ ...s, icon, description });
        this.savingDetails.set(false);
        this.detailsOpen.set(false);
      },
      error: () => this.savingDetails.set(false),
    });
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
    writeSidebarWidth(this.sidebarWidth());
  }

  resetSidebarWidth(): void {
    this.sidebarWidth.set(SIDEBAR_DEFAULT);
    writeSidebarWidth(SIDEBAR_DEFAULT);
  }

  onResizeKeydown(event: KeyboardEvent): void {
    const step = event.shiftKey ? 32 : 16;
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      this.sidebarWidth.update((w) => Math.max(SIDEBAR_MIN, w - step));
      writeSidebarWidth(this.sidebarWidth());
    } else if (event.key === 'ArrowRight') {
      event.preventDefault();
      this.sidebarWidth.update((w) => Math.min(SIDEBAR_MAX, w + step));
      writeSidebarWidth(this.sidebarWidth());
    }
  }

  private reload(): void {
    const s = this.subject();
    if (s) this.load(s.id);
  }
}
