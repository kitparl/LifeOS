import {
  CdkDrag,
  CdkDragDrop,
  CdkDragHandle,
  CdkDragPlaceholder,
  CdkDropList,
} from '@angular/cdk/drag-drop';
import { Component, ElementRef, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import { LucideCircle, LucideCircleCheck, LucideDynamicIcon, provideLucideIcons } from '@lucide/angular';
import { GitHubSectionSyncDisplay } from '../../integrations/services/integrations.service';
import {
  KnowledgeChapter,
  KnowledgeSection,
  KnowledgeSubjectDetail,
} from '../models/knowledge-notes.models';
import { isChapterComplete, isSectionComplete } from '../knowledge-notes.utils';

export type KnowledgeRenameTarget = { kind: 'chapter' | 'section' | 'subject'; id: string };

@Component({
  selector: 'app-knowledge-sidebar',
  standalone: true,
  imports: [
    CdkDropList,
    CdkDrag,
    CdkDragHandle,
    CdkDragPlaceholder,
    LucideDynamicIcon,
  ],
  providers: [provideLucideIcons(LucideCircleCheck, LucideCircle)],
  host: { class: 'contents' },
  template: `
          <aside class="kn-sidebar">
            <div class="flex items-center justify-between px-1 pb-1">
              <span class="section-heading">Chapters</span>
              <button
                type="button"
                class="kn-plus"
                title="New chapter"
                aria-label="New chapter"
                (click)="addChapter.emit()"
              >+</button>
            </div>
            @if (subject.chapters.length === 0) {
              <p class="px-1 text-xs" style="color: var(--text-muted)">No chapters yet.</p>
            }
            <div
              class="kn-chapter-list"
              cdkDropList
              [cdkDropListData]="subject.chapters"
              [cdkDropListConnectedTo]="noConnectedLists"
              (cdkDropListDropped)="chapterDrop.emit($event)"
            >
              @for (c of subject.chapters; track c.id; let ci = $index) {
                <div class="kn-chapter" cdkDrag [cdkDragDisabled]="!!renaming" [class.kn-chapter--closed]="!!c.closed_at">
                  <div class="kn-chapter__head">
                    <span class="kn-drag" title="Drag to reorder" aria-hidden="true" cdkDragHandle>⋮⋮</span>
                    <button
                      type="button"
                      class="kn-chapter__chevron"
                      [attr.aria-expanded]="isExpanded(c.id)"
                      [attr.aria-label]="isExpanded(c.id) ? 'Collapse chapter' : 'Expand chapter'"
                      (click)="toggleChapter.emit({ chapter: c, event: $event })"
                    >{{ isExpanded(c.id) ? '▼' : '▶' }}</button>
                    <span class="kn-index kn-index--chapter" aria-hidden="true">{{ ci + 1 }}</span>
                    <span class="kn-status-slot" aria-hidden="true">
                      @if (chapterStatus(c) === 'done') {
                        <svg class="kn-status-icon kn-status-icon--done" lucideIcon="circle-check" title="Completed"></svg>
                      } @else if (chapterStatus(c) === 'ongoing') {
                        <svg class="kn-status-icon kn-status-icon--ongoing" lucideIcon="circle" title="In progress"></svg>
                      }
                    </span>
                    @if (renaming?.kind === 'chapter' && renaming?.id === c.id) {
                      <input
                        #renameInput
                        type="text"
                        class="kn-inline-input"
                        [value]="c.title"
                        aria-label="Rename chapter"
                        (click)="$event.stopPropagation()"
                        (keydown.enter)="commitRename.emit($event)"
                        (keydown.escape)="cancelRename.emit()"
                        (blur)="commitRename.emit($event)"
                      />
                    } @else {
                      <span
                        class="kn-chapter__title truncate"
                        [class.kn-closed]="!!c.closed_at"
                        title="Click to expand · double-click to rename"
                        (click)="chapterClick.emit({ chapter: c, event: $event })"
                        (dblclick)="startRename.emit({ kind: 'chapter', id: c.id, event: $event })"
                      >{{ c.title }}</span>
                    }
                    <button
                      type="button"
                      class="kn-plus kn-plus--row"
                      title="New section"
                      aria-label="New section"
                      (click)="addSection.emit(c); $event.stopPropagation()"
                    >+</button>
                    <div class="kn-overflow kn-chapter__overflow" [class.is-open]="openMenu === 'chapter:' + c.id">
                      <button
                        type="button"
                        class="kn-overflow__btn kn-overflow__btn--quiet"
                        aria-label="Chapter actions"
                        aria-haspopup="menu"
                        [attr.aria-expanded]="openMenu === 'chapter:' + c.id"
                        (click)="toggleMenu.emit({ id: 'chapter:' + c.id, event: $event })"
                      >⋯</button>
                      @if (openMenu === 'chapter:' + c.id) {
                        <div class="menu kn-overflow__menu" role="menu" (click)="$event.stopPropagation()">
                          <button type="button" class="menu-item" role="menuitem" (click)="startRename.emit({ kind: 'chapter', id: c.id }); closeMenu.emit()">Rename</button>
                          @if (c.closed_at) {
                            <button type="button" class="menu-item" role="menuitem" (click)="toggleChapterClosed.emit({ chapter: c, closed: false }); closeMenu.emit()">Reopen chapter</button>
                          } @else {
                            <button type="button" class="menu-item" role="menuitem" (click)="toggleChapterClosed.emit({ chapter: c, closed: true }); closeMenu.emit()">Mark chapter completed</button>
                          }
                          <button type="button" class="menu-item" role="menuitem" (click)="openChapterDocuments.emit(c); closeMenu.emit()">Documents</button>
                          <button type="button" class="menu-item menu-item--danger" role="menuitem" (click)="deleteChapter.emit(c); closeMenu.emit()">Delete</button>
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
                    [cdkDropListConnectedTo]="sectionListIds"
                    (cdkDropListDropped)="sectionDrop.emit($event)"
                  >
                    @for (sec of c.sections; track sec.id) {
                      <div
                        class="kn-section-row"
                        cdkDrag
                        [cdkDragDisabled]="!!renaming"
                        [class.active]="selected?.id === sec.id"
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
                        @if (renaming?.kind === 'section' && renaming?.id === sec.id) {
                          <input
                            #renameInput
                            type="text"
                            class="kn-inline-input"
                            [value]="sec.title"
                            aria-label="Rename section"
                            (click)="$event.stopPropagation()"
                            (keydown.enter)="commitRename.emit($event)"
                            (keydown.escape)="cancelRename.emit()"
                            (blur)="commitRename.emit($event)"
                          />
                        } @else {
                          <button
                            type="button"
                            class="kn-section-link"
                            [class.active]="selected?.id === sec.id"
                            [class.kn-closed]="!!sec.closed_at"
                            title="Double-click to rename"
                            (click)="selectSection.emit({ section: sec, chapter: c })"
                            (dblclick)="startRename.emit({ kind: 'section', id: sec.id, event: $event })"
                          >{{ sec.title }}</button>
                        }
                        @if (resolveGitHubSyncStatus(sec.id); as ghStatus) {
                          <span
                            class="kn-gh-sync"
                            [attr.data-status]="ghStatus"
                            [title]="githubSyncHint(sec.id)"
                            aria-hidden="true"
                          ></span>
                        }
                        <button
                          type="button"
                          class="kn-section__delete"
                          title="Delete section"
                          aria-label="Delete section"
                          (click)="deleteSection.emit(sec); $event.stopPropagation()"
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
            @if (archivedSections.length > 0) {
              <div class="kn-archived">
                <p class="kn-archived__heading">Archived</p>
                @for (sec of archivedSections; track sec.id) {
                  <div class="kn-archived__row">
                    <div class="min-w-0 flex-1">
                      <p class="kn-archived__title truncate">{{ sec.title }}</p>
                      <p class="kn-archived__meta">Deletes in {{ archiveDaysLeft(sec) }}d</p>
                    </div>
                    <button type="button" class="btn-ghost text-xs" (click)="restoreSection.emit(sec)">Restore</button>
                    <button type="button" class="btn-ghost text-xs" (click)="deletePermanently.emit(sec)">Delete</button>
                  </div>
                }
              </div>
            }
          </aside>
  `,
})
export class KnowledgeSidebarComponent {
  @ViewChild('renameInput') renameInput?: ElementRef<HTMLInputElement>;

  @Input({ required: true }) subject!: KnowledgeSubjectDetail;
  @Input() selected: KnowledgeSection | null = null;
  @Input() renaming: KnowledgeRenameTarget | null = null;
  @Input() openMenu: string | null = null;
  @Input() expandedChapterIds: ReadonlySet<string> = new Set();
  @Input() sectionListIds: string[] = [];
  @Input() archivedSections: KnowledgeSection[] = [];
  @Input() noConnectedLists: string[] = [];
  @Input() githubConfigured = false;
  @Input() sectionSyncStatuses: Record<string, GitHubSectionSyncDisplay> = {};
  @Input() syncState: 'synced' | 'unsaved' | 'saving' = 'synced';

  @Output() readonly addChapter = new EventEmitter<void>();
  @Output() readonly chapterDrop = new EventEmitter<CdkDragDrop<KnowledgeChapter[]>>();
  @Output() readonly sectionDrop = new EventEmitter<CdkDragDrop<KnowledgeSection[]>>();
  @Output() readonly toggleChapter = new EventEmitter<{ chapter: KnowledgeChapter; event: Event }>();
  @Output() readonly chapterClick = new EventEmitter<{ chapter: KnowledgeChapter; event: Event }>();
  @Output() readonly startRename = new EventEmitter<{ kind: 'chapter' | 'section'; id: string; event?: Event }>();
  @Output() readonly commitRename = new EventEmitter<Event>();
  @Output() readonly cancelRename = new EventEmitter<void>();
  @Output() readonly addSection = new EventEmitter<KnowledgeChapter>();
  @Output() readonly toggleMenu = new EventEmitter<{ id: string; event: Event }>();
  @Output() readonly closeMenu = new EventEmitter<void>();
  @Output() readonly toggleChapterClosed = new EventEmitter<{ chapter: KnowledgeChapter; closed: boolean }>();
  @Output() readonly deleteChapter = new EventEmitter<KnowledgeChapter>();
  @Output() readonly openChapterDocuments = new EventEmitter<KnowledgeChapter>();
  @Output() readonly selectSection = new EventEmitter<{ section: KnowledgeSection; chapter: KnowledgeChapter }>();
  @Output() readonly deleteSection = new EventEmitter<KnowledgeSection>();
  @Output() readonly restoreSection = new EventEmitter<KnowledgeSection>();
  @Output() readonly deletePermanently = new EventEmitter<KnowledgeSection>();

  isExpanded(chapterId: string): boolean {
    return this.expandedChapterIds.has(chapterId);
  }

  sectionListId(chapterId: string): string {
    return `kn-sec-${chapterId}`;
  }

  chapterStatus(chapter: KnowledgeChapter): 'done' | 'ongoing' | null {
    if (chapter.sections.length === 0) return null;
    return isChapterComplete(chapter) ? 'done' : 'ongoing';
  }

  sectionStatus(chapter: KnowledgeChapter, sec: KnowledgeSection): 'done' | 'ongoing' {
    return isSectionComplete(chapter, sec) ? 'done' : 'ongoing';
  }

  resolveGitHubSyncStatus(sectionId: string): GitHubSectionSyncDisplay | null {
    if (!this.githubConfigured) return null;
    let status = this.sectionSyncStatuses[sectionId] ?? 'never';
    if (this.selected?.id === sectionId && this.syncState === 'unsaved' && status === 'synced') {
      status = 'outdated';
    }
    return status;
  }

  githubSyncHint(sectionId: string): string {
    const status = this.resolveGitHubSyncStatus(sectionId);
    switch (status) {
      case 'synced':
        return 'Synced to GitHub';
      case 'outdated':
        return 'Needs GitHub sync';
      case 'syncing':
        return 'Syncing to GitHub…';
      case 'failed':
        return 'Last GitHub sync failed';
      default:
        return 'Not synced to GitHub';
    }
  }

  archiveDaysLeft(sec: KnowledgeSection): number {
    const ARCHIVE_TTL_DAYS = 7;
    if (!sec.archived_at) return ARCHIVE_TTL_DAYS;
    const expires = new Date(sec.archived_at).getTime() + ARCHIVE_TTL_DAYS * 24 * 60 * 60 * 1000;
    return Math.max(0, Math.ceil((expires - Date.now()) / (24 * 60 * 60 * 1000)));
  }

  focusRenameInput(): void {
    const el = this.renameInput?.nativeElement;
    if (!el) return;
    el.focus({ preventScroll: true });
    el.select();
  }
}
