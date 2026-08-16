import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
  inject,
} from '@angular/core';
import { Subject, takeUntil } from 'rxjs';
import {
  CodeOutputComponent,
  CodeWorkspaceComponent,
} from '../../shared/code-workspace';
import { CodeExecutionService } from '../../shared/code-workspace/services/code-execution.service';
import { CodeExecutionResult } from '../../shared/code-workspace/models/code-execution.model';
import { EditorDocument } from '../../shared/code-workspace/models/editor-document.model';
import {
  isExecutableLanguage,
  normalizeExecutableLanguage,
} from '../../shared/code-workspace/utils/fenced-code-blocks';
import { CodeBlock, KnowledgeSection } from './models/knowledge-notes.models';
import { KnowledgeNotesService } from './services/knowledge-notes.service';

@Component({
  selector: 'app-knowledge-notes-editor',
  standalone: true,
  imports: [CodeWorkspaceComponent, CodeOutputComponent],
  template: `
    <div class="space-y-2">
      @if (executableBlocks.length > 0) {
        <div class="kn-python">
          @if (executionEnabled) {
            <span class="kn-python__status">Python enabled</span>
            @for (block of executableBlocks; track block.id) {
              <button
                type="button"
                class="btn-secondary text-xs"
                [disabled]="runningBlockId === block.id"
                (click)="onRunCode(block)"
              >
                {{ runningBlockId === block.id ? 'Running…' : 'Run ' + block.language }}
              </button>
            }
            <button type="button" class="btn-ghost text-xs" (click)="executionEnabled = false">
              Disable run
            </button>
          } @else {
            <span class="kn-python__status kn-python__status--off">Python disabled</span>
            <button type="button" class="btn-ghost text-xs" (click)="executionEnabled = true">
              Enable
            </button>
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
            (contentChange)="onContentChange($event)"
            (save)="onSave($event)"
          />
        </div>
      }

      @if (lastResult) {
        <app-code-output
          [result]="lastResult"
          [expanded]="true"
          [maxHeight]="240"
          (cleared)="clearOutput()"
        />
      }
    </div>
  `,
})
export class KnowledgeNotesEditorComponent implements OnChanges, OnDestroy {
  private readonly knowledgeNotes = inject(KnowledgeNotesService);
  private readonly execution = inject(CodeExecutionService);
  private readonly destroy$ = new Subject<void>();

  @Input({ required: true }) section!: KnowledgeSection;

  @Output() contentChange = new EventEmitter<string>();
  @Output() sectionUpdated = new EventEmitter<KnowledgeSection>();
  @Output() saveRequested = new EventEmitter<void>();
  @Output() editorReadyChange = new EventEmitter<void>();

  editorReady = false;
  editorContent = '';
  executionEnabled = true;
  executableBlocks: CodeBlock[] = [];
  runningBlockId: string | null = null;
  lastResult: CodeExecutionResult | null = null;

  private blockResults = new Map<string, CodeExecutionResult>();

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

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
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

  clearOutput(): void {
    this.lastResult = null;
  }

  onRunCode(block: CodeBlock): void {
    if (!this.executionEnabled || this.runningBlockId) {
      return;
    }
    const language = normalizeExecutableLanguage(block.language);
    this.runningBlockId = block.id;
    this.execution
      .execute({
        language,
        code: block.code,
        executionId: `${this.section.id}_${block.id}`,
      })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (result) => this.storeResult(block, result),
        error: (error) =>
          this.storeResult(block, {
            success: false,
            stdout: '',
            stderr: '',
            error: error?.message || 'Execution failed',
            exitCode: 1,
          }),
      });
  }

  private storeResult(block: CodeBlock, result: CodeExecutionResult): void {
    this.runningBlockId = null;
    this.lastResult = result;
    this.blockResults.set(block.id, result);
    block.executionResult = {
      output: result.stdout || result.stderr || '',
      error: result.success ? null : result.error || result.stderr || 'Execution failed',
      executionTime: result.executionTimeMs ?? 0,
      timestamp: new Date(),
    };
  }

  private prepareSection(section: KnowledgeSection): void {
    this.editorReady = false;
    this.lastResult = null;
    this.blockResults.clear();
    this.runningBlockId = null;

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
    const blocks = this.knowledgeNotes.parseCodeBlocks(content);
    this.executableBlocks = blocks.filter((block) => isExecutableLanguage(block.language));
  }
}
