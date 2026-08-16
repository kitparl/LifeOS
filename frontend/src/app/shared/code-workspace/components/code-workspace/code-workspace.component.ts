import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  ViewChild,
  ElementRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, debounceTime, takeUntil } from 'rxjs';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';

import { EditorToolbarComponent, FormatAction, EditorStats } from '../editor-toolbar/editor-toolbar.component';
import { WorkspaceTabsComponent, WorkspaceTab } from '../workspace-tabs/workspace-tabs.component';
import { MarkdownEditorComponent } from '../markdown-editor/markdown-editor.component';
import { MarkdownPreviewComponent } from '../markdown-preview/markdown-preview.component';
import { CodeOutputComponent } from '../code-output/code-output.component';
import { LanguageSelectorComponent } from '../language-selector/language-selector.component';

import { EditorService } from '../../services/editor.service';
import { CodeExecutionService } from '../../services/code-execution.service';
import { ThemeIntegrationService } from '../../services/theme/theme-integration.service';
import { EditorDocument } from '../../models/editor-document.model';
import { CodeExecutionRequest, CodeExecutionResult } from '../../models/code-execution.model';
import {
  isExecutableLanguage,
  normalizeExecutableLanguage,
  parseFencedCodeBlocks,
} from '../../utils/fenced-code-blocks';

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
  ],
  templateUrl: './code-workspace.component.html',
  styleUrls: ['./code-workspace.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    role: 'region',
    'aria-label': 'Code workspace',
  },
})
export class CodeWorkspaceComponent implements OnInit, OnDestroy {
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

  // ========== OUTPUTS ==========
  
  @Output() contentChange = new EventEmitter<string>();
  @Output() run = new EventEmitter<CodeExecutionRequest>();
  @Output() save = new EventEmitter<EditorDocument>();

  // ========== STATE ==========
  
  currentContent: string = '';
  currentLanguage: string = 'markdown';
  currentView: WorkspaceTab = 'edit';
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
  @ViewChild(MarkdownEditorComponent) markdownEditor?: MarkdownEditorComponent;

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
    this.updateStats(this.currentContent);

    // Setup responsive breakpoints
    this.setupBreakpoints();

    // Setup content change debouncing
    this.contentChange$
      .pipe(
        debounceTime(300),
        takeUntil(this.destroy$)
      )
      .subscribe((content) => {
        this.updateStats(content);
        this.contentChange.emit(content);
      });

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
        
        this.isMobile = breakpoints[Breakpoints.HandsetPortrait] || 
                        breakpoints[Breakpoints.HandsetLandscape];
        
        this.isTablet = breakpoints[Breakpoints.TabletPortrait] || 
                        breakpoints[Breakpoints.TabletLandscape];
        
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
  
  onFormatAction(action: FormatAction): void {
    this.markdownEditor?.applyFormat(action);
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

  shouldShowSplitView(): boolean {
    return this.isDesktop && this.showPreview;
  }

  shouldShowEditor(): boolean {
    return !this.isMobile || this.currentView === 'edit';
  }

  shouldShowPreview(): boolean {
    if (!this.showPreview) return false;
    if (this.isMobile) return this.currentView === 'preview';
    return this.isDesktop;
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
