import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  HostListener,
  Input,
  OnChanges,
  OnDestroy,
  OnInit,
  Output,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, debounceTime, takeUntil } from 'rxjs';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';

import { EditorToolbarComponent, FormatAction, EditorStats, WorkspaceViewMode, SplitOrientation } from '../editor-toolbar/editor-toolbar.component';
import { WorkspaceTabsComponent, WorkspaceTab } from '../workspace-tabs/workspace-tabs.component';
import { MarkdownEditorComponent } from '../markdown-editor/markdown-editor.component';
import { MarkdownPreviewComponent } from '../markdown-preview/markdown-preview.component';
import { CodeOutputComponent } from '../code-output/code-output.component';
import { SplitBounds, SplitDividerComponent } from '../../../split-divider/split-divider.component';
import { LanguageSelectorComponent } from '../language-selector/language-selector.component';

import { EditorService } from '../../services/editor.service';
import { CodeExecutionService } from '../../services/code-execution.service';
import { ThemeIntegrationService } from '../../services/theme/theme-integration.service';
import { EditorDocument } from '../../models/editor-document.model';
import { CodeExecutionRequest, CodeExecutionResult } from '../../models/code-execution.model';
import {
  ParsedCodeBlock,
  isExecutableLanguage,
  normalizeExecutableLanguage,
  parseFencedCodeBlocks,
} from '../../utils/fenced-code-blocks';
import { filesFromClipboard, filesFromDataTransfer } from '../../../file-upload/clipboard-files';

/**
 * Main container component for the Code Workspace.
 * 
 * Orchestrates all child components:
 * - EditorToolbarComponent (formatting)
 * - WorkspaceTabsComponent (mobile navigation)
 * - MarkdownEditorComponent (CodeMirror)
 * - MarkdownPreviewComponent (live preview)
 * - CodeOutputComponent (execution results)
 * - LanguageSelectorComponent (language picker)
 * 
 * Manages:
 * - Responsive layouts (desktop split view, mobile tabs)
 * - State (content, language, view, execution)
 * - Autosave coordination
 * - Configuration API
 */
@Component({
  selector: 'app-code-workspace',
  standalone: true,
  imports: [
    CommonModule,
    EditorToolbarComponent,
    WorkspaceTabsComponent,
    MarkdownEditorComponent,
    MarkdownPreviewComponent,
    CodeOutputComponent,
    LanguageSelectorComponent,
    SplitDividerComponent,
  ],
  templateUrl: './code-workspace.component.html',
  styleUrls: ['./code-workspace.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    role: 'region',
    'aria-label': 'Code workspace',
    '[class.fullscreen]': 'fullscreen',
  },
})
export class CodeWorkspaceComponent implements OnInit, OnChanges, OnDestroy {
  // ========== INPUTS ==========
  
  @Input() content: string = '';
  @Input() mode: 'markdown' | 'code' | 'markdown-code' = 'markdown';
  @Input() language: string = 'markdown';
  @Input() showPreview: boolean = true;
  @Input() showToolbar: boolean = true;
  @Input() showRunButton: boolean = true;
  @Input() showLanguageSelector: boolean = true;
  @Input() showWordCount: boolean = true;
  @Input() showOutput: boolean = true;
  @Input() enableAutosave: boolean = false;
  @Input() enableFileImport: boolean = false;
  @Input() enableFileExport: boolean = false;
  @Input() readOnly: boolean = false;
  @Input() theme: 'light' | 'dark' | 'system' = 'system';
  @Input() defaultViewMode: WorkspaceViewMode = 'write';
  @Input() previewVariant: 'default' | 'journal' = 'default';
  @Input() enableFilePaste = false;
  /** Executable fences that get an inline Run button in the preview (opt-in). */
  @Input() runnableBlocks: ParsedCodeBlock[] = [];
  @Input() runningBlockId: string | null = null;
  @Input() runDisabled = false;

  // ========== OUTPUTS ==========
  
  @Output() contentChange = new EventEmitter<string>();
  @Output() run = new EventEmitter<CodeExecutionRequest>();
  @Output() save = new EventEmitter<EditorDocument>();
  @Output() filesPasted = new EventEmitter<File[]>();
  @Output() runBlock = new EventEmitter<ParsedCodeBlock>();

  // ========== STATE ==========
  
  currentContent: string = '';
  currentLanguage: string = 'markdown';
  currentView: WorkspaceTab = 'edit';
  viewMode: WorkspaceViewMode = 'write';
  splitOrientation: SplitOrientation = 'horizontal';
  /** Editor share of the split (0.2–0.8). Default is 50/50. */
  splitRatio = 0.5;
  resizing = false;
  fullscreen = false;
  editorStats: EditorStats = {
    wordCount: 0,
    charCount: 0,
    lineCount: 0,
  };
  executionResult: CodeExecutionResult | null = null;
  isExecuting: boolean = false;
  currentExecutionId: string | null = null;
  themeReady = false;

  // Responsive state
  isMobile: boolean = false;
  isTablet: boolean = false;
  isDesktop: boolean = false;

  // Subjects
  private destroy$ = new Subject<void>();
  private contentChange$ = new Subject<string>();

  @ViewChild('editorContainer') editorContainer?: ElementRef;
  @ViewChild('workspaceContent') workspaceContent?: ElementRef<HTMLElement>;
  @ViewChild(MarkdownEditorComponent) markdownEditor?: MarkdownEditorComponent;

  readonly splitMin = 0.2;
  readonly splitMax = 0.8;

  constructor(
    private breakpointObserver: BreakpointObserver,
    private editorService: EditorService,
    private codeExecutionService: CodeExecutionService,
    private themeIntegration: ThemeIntegrationService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.currentContent = this.content;
    this.currentLanguage = this.language;
    this.viewMode = this.defaultViewMode;
    this.updateStats(this.currentContent);

    // Setup responsive breakpoints
    this.setupBreakpoints();

    // Autosave after idle (stats and contentChange are updated immediately)
    this.contentChange$
      .pipe(
        debounceTime(1500),
        takeUntil(this.destroy$)
      )
      .subscribe(() => {
        if (this.enableAutosave) {
          this.onSave();
        }
      });

    this.themeIntegration.resolvedTheme$
      .pipe(takeUntil(this.destroy$))
      .subscribe((theme) => {
        this.theme = theme;
        this.markdownEditor?.setTheme(theme);
        this.cdr.markForCheck();
      });

    queueMicrotask(() => {
      this.themeReady = true;
      this.cdr.markForCheck();
    });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['content'] || changes['content'].firstChange) {
      return;
    }
    const next = this.content ?? '';
    if (next === this.currentContent) {
      return;
    }
    this.currentContent = next;
    this.updateStats(next);
    this.markdownEditor?.setContent(next);
    this.cdr.markForCheck();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ========== RESPONSIVE LAYOUT ==========
  
  private setupBreakpoints(): void {
    this.breakpointObserver
      .observe([
        Breakpoints.HandsetPortrait,
        Breakpoints.HandsetLandscape,
        Breakpoints.TabletPortrait,
        Breakpoints.TabletLandscape,
        Breakpoints.Web,
      ])
      .pipe(takeUntil(this.destroy$))
      .subscribe((result) => {
        const breakpoints = result.breakpoints;
        
        this.isMobile = breakpoints[Breakpoints.HandsetPortrait];
        
        this.isTablet = breakpoints[Breakpoints.TabletPortrait] || 
                        breakpoints[Breakpoints.TabletLandscape] ||
                        breakpoints[Breakpoints.HandsetLandscape];
        
        this.isDesktop = breakpoints[Breakpoints.Web];

        // On mobile, default to tabs view
        if (this.isMobile && this.currentView !== 'edit') {
          // Keep current view
        }

        this.cdr.markForCheck();
      });
  }

  // ========== CONTENT MANAGEMENT ==========
  
  onContentChange(content: string): void {
    this.currentContent = content;
    this.updateStats(content);
    this.contentChange.emit(content);
    this.contentChange$.next(content);
  }

  private updateStats(content: string): void {
    const lines = content.split('\n');
    const words = content.trim().split(/\s+/).filter(w => w.length > 0);
    
    this.editorStats = {
      wordCount: words.length,
      charCount: content.length,
      lineCount: lines.length,
    };

    this.cdr.markForCheck();
  }

  // ========== TOOLBAR ACTIONS ==========
  
  insertAtCursor(text: string): void {
    if (this.markdownEditor) {
      this.markdownEditor.insertAtCursor(text);
      return;
    }
    const next = this.currentContent
      ? `${this.currentContent}\n${text}`
      : text;
    this.onContentChange(next);
  }

  setContent(content: string): void {
    this.currentContent = content;
    this.updateStats(content);
    this.markdownEditor?.setContent(content);
    this.cdr.markForCheck();
  }

  onEditorPaste(event: ClipboardEvent): void {
    if (!this.enableFilePaste) return;
    const files = filesFromClipboard(event);
    if (!files.length) return;
    event.preventDefault();
    event.stopPropagation();
    this.filesPasted.emit(files);
  }

  onEditorDragOver(event: DragEvent): void {
    if (!this.enableFilePaste) return;
    const types = event.dataTransfer?.types;
    if (!types || !Array.from(types).includes('Files')) return;
    event.preventDefault();
    event.stopPropagation();
  }

  onEditorDragLeave(event: DragEvent): void {
    if (!this.enableFilePaste) return;
    event.preventDefault();
  }

  onEditorDrop(event: DragEvent): void {
    if (!this.enableFilePaste) return;
    const files = filesFromDataTransfer(event.dataTransfer);
    if (!files.length) return;
    event.preventDefault();
    event.stopPropagation();
    this.filesPasted.emit(files);
  }

  onFormatAction(action: FormatAction): void {
    this.markdownEditor?.applyFormat(action);
  }

  onViewModeChange(mode: WorkspaceViewMode): void {
    this.viewMode = mode;
    this.cdr.markForCheck();
  }

  onSplitOrientationChange(orientation: SplitOrientation): void {
    this.splitOrientation = orientation;
    this.cdr.markForCheck();
  }

  get splitColumns(): string | null {
    if (!this.shouldShowSplitView() || this.splitOrientation !== 'horizontal') return null;
    return `minmax(0, ${this.splitRatio}fr) auto minmax(0, ${1 - this.splitRatio}fr)`;
  }

  get splitRows(): string | null {
    if (!this.shouldShowSplitView() || this.splitOrientation !== 'vertical') return null;
    return `minmax(0, ${this.splitRatio}fr) auto minmax(0, ${1 - this.splitRatio}fr) auto`;
  }

  resetSplitRatio(): void {
    this.resizing = false;
    this.splitRatio = 0.5;
    this.cdr.markForCheck();
  }

  onSplitChange(ratio: number): void {
    this.splitRatio = ratio;
    this.cdr.markForCheck();
  }

  /** Extent of the editor and preview panes along the split axis, read while dragging. */
  readonly splitBounds = (): SplitBounds | null => {
    const root = this.workspaceContent?.nativeElement;
    const editor = root?.querySelector('.editor-panel')?.getBoundingClientRect();
    const preview = root?.querySelector('.preview-panel')?.getBoundingClientRect();
    if (!editor || !preview) return null;
    return this.splitOrientation === 'horizontal'
      ? { start: editor.left, end: preview.right }
      : { start: editor.top, end: preview.bottom };
  };

  toggleFullscreen(): void {
    this.fullscreen = !this.fullscreen;
    this.cdr.markForCheck();
  }

  @HostListener('document:keydown.escape', ['$event'])
  onEscape(event?: KeyboardEvent): void {
    if (!this.fullscreen) return;
    if (event?.defaultPrevented) return;
    const target = event?.target as HTMLElement | null;
    if (target?.closest('dialog, [role="dialog"], .modal, app-modal')) return;
    if (document.querySelector('.modal-backdrop, [role="dialog"]')) return;
    this.fullscreen = false;
    this.cdr.markForCheck();
  }

  // ========== LANGUAGE SELECTION ==========
  
  onLanguageChange(language: string | { id: string }): void {
    this.currentLanguage = typeof language === 'string' ? language : language.id;
    this.cdr.markForCheck();
  }

  // ========== CODE EXECUTION ==========
  
  onRunCode(): void {
    const snippet = this.resolveRunnableSnippet();
    if (!snippet) return;
    this.runRequest(snippet.code, snippet.language);
  }

  /**
   * Execute a snippet (used by markdown-code mode and knowledge notes).
   */
  executeCode(code: string, language: string): void {
    this.runRequest(code, language);
  }

  private runRequest(code: string, language: string): void {
    const mapped = normalizeExecutableLanguage(language);
    if (this.isExecuting || !this.codeExecutionService.isExecutionSupported(mapped)) {
      return;
    }

    this.isExecuting = true;
    this.currentExecutionId = this.generateExecutionId();

    const request: CodeExecutionRequest = {
      language: mapped,
      code,
      executionId: this.currentExecutionId,
    };

    this.run.emit(request);

    this.codeExecutionService
      .execute(request)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (result) => {
          this.executionResult = result;
          this.isExecuting = false;
          this.currentExecutionId = null;

          if (this.isMobile) {
            this.currentView = 'output';
          }

          this.cdr.markForCheck();
        },
        error: (error) => {
          this.executionResult = {
            success: false,
            stdout: '',
            stderr: '',
            error: error.message || 'Execution failed',
            exitCode: 1,
          };
          this.isExecuting = false;
          this.currentExecutionId = null;
          this.cdr.markForCheck();
        },
      });
  }

  private resolveRunnableSnippet(): { code: string; language: string } | null {
    if (this.mode === 'markdown-code' || this.currentLanguage === 'markdown') {
      const block = parseFencedCodeBlocks(this.currentContent).find((item) =>
        isExecutableLanguage(item.language)
      );
      if (block) {
        return { code: block.code, language: block.language };
      }
      return null;
    }
    if (!this.codeExecutionService.isExecutionSupported(this.currentLanguage)) {
      return null;
    }
    return { code: this.currentContent, language: this.currentLanguage };
  }

  onStopExecution(): void {
    if (this.currentExecutionId) {
      this.codeExecutionService.stop(this.currentExecutionId, this.currentLanguage);
      this.isExecuting = false;
      this.currentExecutionId = null;
      this.cdr.markForCheck();
    }
  }

  onOutputCleared(): void {
    this.executionResult = null;
    this.cdr.markForCheck();
  }

  canExecute(): boolean {
    return this.resolveRunnableSnippet() !== null;
  }

  // ========== TAB NAVIGATION (Mobile) ==========
  
  onTabChange(tab: WorkspaceTab): void {
    this.currentView = tab;
    this.cdr.markForCheck();
  }

  // ========== SAVE ==========
  
  onSave(): void {
    const document: EditorDocument = {
      title: 'Untitled',
      content: this.currentContent,
      format: this.mode === 'code' ? 'code' : 'markdown',
      language: this.currentLanguage,
      updatedAt: new Date().toISOString(),
    };

    this.save.emit(document);
  }

  // ========== HELPERS ==========
  
  private generateExecutionId(): string {
    return `exec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // ========== VIEW GETTERS ==========
  
  shouldShowTabs(): boolean {
    return this.isMobile;
  }

  shouldShowViewModes(): boolean {
    return this.showPreview && !this.isMobile;
  }

  shouldShowSplitView(): boolean {
    return !this.isMobile && this.showPreview && this.viewMode === 'split';
  }

  shouldShowEditor(): boolean {
    if (this.isMobile) return this.currentView === 'edit';
    if (!this.showPreview) return true;
    return this.viewMode !== 'preview';
  }

  shouldShowPreview(): boolean {
    if (!this.showPreview) return false;
    if (this.isMobile) return this.currentView === 'preview';
    return this.viewMode !== 'write';
  }

  shouldShowOutput(): boolean {
    if (!this.showOutput) return false;
    if (this.isMobile) return this.currentView === 'output';
    return this.executionResult !== null;
  }

  getRunButtonLabel(): string {
    return this.isExecuting ? 'Stop' : 'Run';
  }

  get resolvedTheme(): 'light' | 'dark' {
    if (this.theme === 'dark') {
      return 'dark';
    }
    return 'light';
  }

  isRunButtonDisabled(): boolean {
    return !this.canExecute() || (this.isExecuting && this.currentExecutionId === null);
  }
}
