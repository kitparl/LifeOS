import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  ViewChild,
  inject,
} from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MarkdownImportButtonComponent } from '../../../shared/markdown/markdown-import-button.component';
import { MarkdownImportResult } from '../../../shared/markdown/markdown-import.service';
import { MarkdownExportButtonComponent } from '../../../shared/markdown/markdown-export-button.component';
import { MarkdownPipe } from '../../../shared/markdown/markdown.pipe';
import { FileImageSrcDirective } from '../../../shared/markdown/file-image-src.directive';
import { AttachmentListComponent } from '../../files/components/attachment-list.component';
import { FileRecord } from '../../files/models/file.models';
import { GitHubSectionSyncDisplay } from '../../integrations/services/integrations.service';
import { KnowledgeNotesEditorComponent } from '../knowledge-notes-editor.component';
import { GitHubSyncButtonComponent } from '../github-sync-button.component';
import { CodeBlock, KnowledgeSection } from '../models/knowledge-notes.models';
import { CodeOutputComponent } from '../../../shared/code-workspace/components/code-output/code-output.component';
import { RunnableFencesDirective } from '../../../shared/code-workspace/directives/runnable-fences.directive';
import { KnowledgeNotesService } from '../services/knowledge-notes.service';
import { KnowledgeCodeRunnerService } from '../services/knowledge-code-runner.service';
import { KnowledgeRunBarComponent } from './knowledge-run-bar.component';

@Component({
  selector: 'app-knowledge-section-editor',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    KnowledgeNotesEditorComponent,
    MarkdownPipe,
    FileImageSrcDirective,
    AttachmentListComponent,
    MarkdownImportButtonComponent,
    MarkdownExportButtonComponent,
    GitHubSyncButtonComponent,
    KnowledgeRunBarComponent,
    RunnableFencesDirective,
    CodeOutputComponent,
  ],
  providers: [KnowledgeCodeRunnerService],
  host: { class: 'contents' },
  template: `
          <section class="kn-main">
            @if (section; as sec) {
              <form [formGroup]="form" class="space-y-2">
                <div class="kn-docbar">
                  @if (previewOnly) {
                    <h2 class="kn-section-title-read">{{ form.controls.title.value }}</h2>
                  } @else {
                    <input class="kn-section-title" formControlName="title" placeholder="Section title" />
                  }
                  <div class="kn-docbar__actions">
                    @if (importError) {
                      <span class="text-xs" style="color: var(--danger)">{{ importError }}</span>
                    }
                    <app-markdown-import-button
                      [currentContent]="form.controls.content.value"
                      [currentTitle]="form.controls.title.value"
                      (imported)="markdownImported.emit($event)"
                      (importError)="markdownImportError.emit($event)"
                    />
                    <app-markdown-export-button
                      [content]="form.controls.content.value"
                      [filename]="form.controls.title.value || 'section'"
                      (exportError)="markdownImportError.emit($event)"
                    />
                    @if (resolveGitHubSyncStatus(sec.id); as ghStatus) {
                      <span
                        class="kn-gh-sync kn-gh-sync--label"
                        [attr.data-status]="ghStatus"
                        [title]="githubSyncHint(sec.id)"
                      >{{ githubSyncShortLabel(ghStatus) }}</span>
                    }
                    <app-github-sync-button
                      [sectionId]="sec.id"
                      [configured]="githubConfigured"
                      [disabled]="syncState === 'saving'"
                      [beforeSync]="beforeSync"
                      (syncSuccess)="gitHubSyncSuccess.emit({ message: $event, sectionId: sec.id })"
                      (syncError)="gitHubSyncError.emit($event)"
                    />
                    @if (githubMessage && githubMessageSectionId === sec.id) {
                      <span class="text-xs" style="color: var(--success)">{{ githubMessage }}</span>
                    }
                    @if (previewOnly) {
                      <button type="button" class="btn-primary text-xs" (click)="enterEditMode.emit()">Edit</button>
                    } @else {
                      <span class="kn-sync" [attr.data-state]="syncState" aria-live="polite">
                        @switch (syncState) {
                          @case ('saving') { Saving… }
                          @case ('unsaved') { Unsaved }
                          @default { Synced }
                        }
                      </span>
                      <button
                        type="button"
                        class="btn-primary text-xs"
                        [disabled]="syncState !== 'unsaved'"
                        (click)="save.emit()"
                      >Save</button>
                      <button type="button" class="btn-secondary text-xs" (click)="cancelEdit.emit()">Cancel</button>
                    }
                    <div class="kn-overflow">
                      <button
                        type="button"
                        class="btn-ghost kn-overflow__btn"
                        aria-label="Section actions"
                        aria-haspopup="menu"
                        [attr.aria-expanded]="openMenu === 'section'"
                        (click)="toggleMenu.emit({ id: 'section', event: $event })"
                      >⋯</button>
                      @if (openMenu === 'section') {
                        <div class="menu kn-overflow__menu" role="menu" (click)="$event.stopPropagation()">
                          <button type="button" class="menu-item" role="menuitem" (click)="exportSectionMarkdown.emit(); closeMenu.emit()">Export to MD</button>
                          @if (sec.closed_at) {
                            <button type="button" class="menu-item" role="menuitem" (click)="toggleSectionClosed.emit({ section: sec, closed: false }); closeMenu.emit()">Reopen section</button>
                          } @else {
                            <button type="button" class="menu-item" role="menuitem" (click)="toggleSectionClosed.emit({ section: sec, closed: true }); closeMenu.emit()">Mark section completed</button>
                          }
                          <button type="button" class="menu-item menu-item--danger" role="menuitem" (click)="deleteSection.emit(sec); closeMenu.emit()">Delete</button>
                        </div>
                      }
                    </div>
                  </div>
                </div>
                @if (previewOnly) {
                  <div class="space-y-2">
                    <app-knowledge-run-bar [blocks]="viewBlocks" [sectionId]="sec.id" />
                    <div
                      class="markdown-body panel"
                      appFileImageSrc
                      [appRunnableFences]="viewBlocks"
                      [runningFenceId]="runner.runningBlockId()"
                      [fenceRunDisabled]="!runner.enabled()"
                      (fenceRun)="runner.run(sec.id, $event)"
                      [innerHTML]="form.controls.content.value | markdown"
                    ></div>
                    @if (runner.lastResult(); as result) {
                      <app-code-output
                        [result]="result"
                        [expanded]="true"
                        [maxHeight]="240"
                        (cleared)="runner.clear()"
                      />
                    }
                  </div>
                } @else {
                  <app-knowledge-notes-editor
                    [section]="sec"
                    (contentChange)="editorContentChange.emit($event)"
                    (sectionUpdated)="editorSaved.emit($event)"
                    (saveRequested)="save.emit()"
                    (editorReadyChange)="editorReady.emit()"
                    (filesChanged)="inlineFilesChanged.emit()"
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
                    (removed)="documentRemoved.emit($event)"
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
  `,
})
export class KnowledgeSectionEditorComponent implements OnChanges {
  private readonly knowledgeNotes = inject(KnowledgeNotesService);
  readonly runner = inject(KnowledgeCodeRunnerService);

  @ViewChild(KnowledgeNotesEditorComponent) editor?: KnowledgeNotesEditorComponent;
  @ViewChild('historyList') historyList?: AttachmentListComponent;

  @Input() section: KnowledgeSection | null = null;
  @Input({ required: true }) form!: FormGroup<{
    title: FormControl<string>;
    content: FormControl<string>;
  }>;
  @Input() previewOnly = false;
  @Input() syncState: 'synced' | 'unsaved' | 'saving' = 'synced';
  @Input() importError = '';
  @Input() githubConfigured = false;
  @Input() githubMessage: string | null = null;
  @Input() githubMessageSectionId: string | null = null;
  @Input() sectionSyncStatuses: Record<string, GitHubSectionSyncDisplay> = {};
  @Input() openMenu: string | null = null;
  @Input() beforeSync: (() => Promise<void>) | null = null;

  @Output() readonly markdownImported = new EventEmitter<MarkdownImportResult>();
  @Output() readonly markdownImportError = new EventEmitter<string>();
  @Output() readonly gitHubSyncSuccess = new EventEmitter<{ message: string; sectionId: string }>();
  @Output() readonly gitHubSyncError = new EventEmitter<string>();
  @Output() readonly enterEditMode = new EventEmitter<void>();
  @Output() readonly save = new EventEmitter<void>();
  @Output() readonly cancelEdit = new EventEmitter<void>();
  @Output() readonly toggleMenu = new EventEmitter<{ id: string; event: Event }>();
  @Output() readonly closeMenu = new EventEmitter<void>();
  @Output() readonly exportSectionMarkdown = new EventEmitter<void>();
  @Output() readonly toggleSectionClosed = new EventEmitter<{ section: KnowledgeSection; closed: boolean }>();
  @Output() readonly deleteSection = new EventEmitter<KnowledgeSection>();
  @Output() readonly editorContentChange = new EventEmitter<string>();
  @Output() readonly editorSaved = new EventEmitter<KnowledgeSection>();
  @Output() readonly editorReady = new EventEmitter<void>();
  @Output() readonly inlineFilesChanged = new EventEmitter<void>();
  @Output() readonly documentRemoved = new EventEmitter<FileRecord>();

  private viewBlocksContent: string | null = null;
  private viewBlocksCache: CodeBlock[] = [];

  ngOnChanges(changes: SimpleChanges): void {
    const change = changes['section'];
    const previous = change?.previousValue as KnowledgeSection | null | undefined;
    if (change && previous?.id !== this.section?.id) {
      this.runner.reset();
    }
  }

  /** Executable blocks for view mode; stable reference while content is unchanged. */
  get viewBlocks(): CodeBlock[] {
    const content = this.form.controls.content.value ?? '';
    if (content !== this.viewBlocksContent) {
      this.viewBlocksContent = content;
      this.viewBlocksCache = this.knowledgeNotes.executableCodeBlocks(content);
    }
    return this.viewBlocksCache;
  }

  resolveGitHubSyncStatus(sectionId: string): GitHubSectionSyncDisplay | null {
    if (!this.githubConfigured) return null;
    let status = this.sectionSyncStatuses[sectionId] ?? 'never';
    if (this.section?.id === sectionId && this.syncState === 'unsaved' && status === 'synced') {
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

  githubSyncShortLabel(status: GitHubSectionSyncDisplay): string {
    switch (status) {
      case 'synced':
        return 'Synced';
      case 'outdated':
        return 'Needs sync';
      case 'syncing':
        return 'Syncing…';
      case 'failed':
        return 'Sync failed';
      default:
        return 'Not synced';
    }
  }

  setContent(content: string): void {
    this.editor?.setContent(content);
  }

  reloadHistory(): void {
    this.historyList?.load();
  }
}
