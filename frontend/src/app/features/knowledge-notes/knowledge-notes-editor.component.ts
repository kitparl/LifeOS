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
import { firstValueFrom } from 'rxjs';
import {
  CodeOutputComponent,
  CodeWorkspaceComponent,
} from '../../shared/code-workspace';
import { EditorDocument } from '../../shared/code-workspace/models/editor-document.model';
import { FilesService } from '../files/services/files.service';
import { FileRecord } from '../files/models/file.models';
import { CodeBlock, KnowledgeSection } from './models/knowledge-notes.models';
import { KnowledgeNotesService } from './services/knowledge-notes.service';
import { KnowledgeCodeRunnerService } from './services/knowledge-code-runner.service';
import { KnowledgeRunBarComponent } from './components/knowledge-run-bar.component';

@Component({
  selector: 'app-knowledge-notes-editor',
  standalone: true,
  imports: [CodeWorkspaceComponent, CodeOutputComponent, KnowledgeRunBarComponent],
  template: `
    <div class="space-y-2">
      <app-knowledge-run-bar [blocks]="executableBlocks" [sectionId]="section.id" [showPicker]="true" />

      @if (uploadStatus || uploadError) {
        <div class="kn-python">
          @if (uploadStatus) {
            <span class="kn-python__status">{{ uploadStatus }}</span>
          }
          @if (uploadError) {
            <span class="kn-python__status" style="color: var(--danger)">{{ uploadError }}</span>
          }
        </div>
      }

      @if (editorReady) {
        <div class="kn-editor-frame">
          <app-code-workspace
            [content]="editorContent"
            mode="markdown-code"
            language="markdown"
            [showPreview]="true"
            [showToolbar]="true"
            [showRunButton]="false"
            [showLanguageSelector]="false"
            [showOutput]="false"
            defaultViewMode="write"
            [enableAutosave]="false"
            [enableFilePaste]="true"
            (contentChange)="onContentChange($event)"
            (save)="onSave($event)"
            (filesPasted)="onFilesPasted($event)"
            [runnableBlocks]="executableBlocks"
            [runningBlockId]="runner.runningBlockId()"
            [runDisabled]="!runner.enabled()"
            (runBlock)="onRunCode($event)"
          />
        </div>
      }

      @if (runner.lastResult(); as result) {
        <app-code-output
          [result]="result"
          [expanded]="true"
          [maxHeight]="240"
          (cleared)="runner.clear()"
        />
      }
    </div>
  `,
})
export class KnowledgeNotesEditorComponent implements OnChanges {
  private readonly knowledgeNotes = inject(KnowledgeNotesService);
  readonly runner = inject(KnowledgeCodeRunnerService);
  private readonly filesService = inject(FilesService);

  @ViewChild(CodeWorkspaceComponent) workspace?: CodeWorkspaceComponent;

  @Input({ required: true }) section!: KnowledgeSection;

  @Output() contentChange = new EventEmitter<string>();
  @Output() sectionUpdated = new EventEmitter<KnowledgeSection>();
  @Output() saveRequested = new EventEmitter<void>();
  @Output() editorReadyChange = new EventEmitter<void>();
  @Output() filesChanged = new EventEmitter<void>();

  editorReady = false;
  editorContent = '';
  executableBlocks: CodeBlock[] = [];
  uploadStatus = '';
  uploadError = '';

  ngOnChanges(changes: SimpleChanges): void {
    const change = changes['section'];
    if (!change || !this.section) {
      return;
    }
    const previous = change.previousValue as KnowledgeSection | undefined;
    if (!change.firstChange && previous?.id === this.section.id) {
      return;
    }
    this.prepareSection(this.section);
  }

  onContentChange(content: string): void {
    if (!this.editorReady) {
      return;
    }
    this.editorContent = content;
    this.refreshBlocks(content);
    this.contentChange.emit(content);
  }

  onSave(document: EditorDocument): void {
    this.onContentChange(document.content);
    this.saveRequested.emit();
  }

  async onFilesPasted(files: File[]): Promise<void> {
    if (!files.length || !this.section?.id) return;
    this.uploadError = '';
    this.uploadStatus = files.length === 1 ? 'Uploading…' : `Uploading ${files.length} files…`;
    for (const file of files) {
      try {
        const record = await firstValueFrom(
          this.filesService.upload(file, 'knowledge_notes', this.section.id)
        );
        this.workspace?.insertAtCursor(this.markdownForRecord(record, file));
      } catch (err: unknown) {
        const detail = (err as { error?: { detail?: string } })?.error?.detail;
        this.uploadError = detail || 'Upload failed';
        this.uploadStatus = '';
        return;
      }
    }
    this.uploadStatus = '';
    this.filesChanged.emit();
  }

  setContent(content: string): void {
    this.editorContent = content;
    this.refreshBlocks(content);
    this.workspace?.setContent(content);
  }

  private markdownForRecord(record: FileRecord, file: File): string {
    const name = (record.filename || file.name || 'file').replace(/]/g, '');
    const url = record.url || `/api/v1/files/${record.id}/content`;
    const type = record.content_type || file.type || '';
    return type.startsWith('image/') ? `![${name}](${url})` : `[${name}](${url})`;
  }

  onRunCode(block: CodeBlock): void {
    this.runner.run(this.section.id, block);
  }

  private prepareSection(section: KnowledgeSection): void {
    this.editorReady = false;
    this.uploadStatus = '';
    this.uploadError = '';

    const prepared = this.knowledgeNotes.enrichSection(section);
    this.editorContent = prepared.content ?? '';
    this.refreshBlocks(this.editorContent);
    this.contentChange.emit(this.editorContent);
    queueMicrotask(() => {
      if (this.section?.id !== section.id) {
        return;
      }
      this.editorReady = true;
      this.editorReadyChange.emit();
    });
  }

  private refreshBlocks(content: string): void {
    this.executableBlocks = this.knowledgeNotes.executableCodeBlocks(content);
  }
}
