import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnDestroy,
  ElementRef,
  ViewChild,
  AfterViewInit,
  effect,
  inject,
  signal,
} from '@angular/core';
import { EditorView } from 'codemirror';
import { EditorService } from '../../services/editor.service';
import { EditorConfig } from '../../models';
import { FormatAction } from '../editor-toolbar/editor-toolbar.component';
import { EditorPreferencesService } from '../../../../core/services/editor-preferences.service';

type VimModeLabel = 'NORMAL' | 'INSERT' | 'VISUAL' | 'REPLACE';

@Component({
  selector: 'app-markdown-editor',
  standalone: true,
  template: `
    <div
      #editorContainer
      class="editor-container"
      [class.read-only]="readOnly"
      [class.vim-keymap-active]="editorPrefs.keymap() === 'vim'"
    >
      @if (vimModeLabel()) {
        <span class="vim-mode-badge">{{ vimModeLabel() }}</span>
      }
    </div>
  `,
  styles: [`
    .editor-container {
      position: relative;
      height: 100%;
      width: 100%;
      overflow: hidden;
      min-height: 0;
      touch-action: pan-x pan-y;
    }
    
    .read-only {
      opacity: 0.8;
      cursor: not-allowed;
    }

    :host {
      display: block;
      height: 100%;
      width: 100%;
      min-height: 0;
    }

    .editor-container :deep(.cm-editor) {
      height: 100%;
      min-height: 0;
    }

    .editor-container :deep(.cm-scroller) {
      overflow: auto;
    }

    .vim-mode-badge {
      position: absolute;
      right: 0.5rem;
      bottom: 0.375rem;
      z-index: 2;
      padding: 0.125rem 0.375rem;
      font-size: 0.6875rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      color: var(--text-muted);
      background: var(--surface-2);
      border: 1px solid var(--border);
      border-radius: 3px;
      pointer-events: none;
      user-select: none;
    }
  `]
})
export class MarkdownEditorComponent implements AfterViewInit, OnDestroy {
  @ViewChild('editorContainer', { static: true }) editorContainer!: ElementRef<HTMLElement>;

  @Input() content = '';
  @Input() language = 'markdown';
  @Input() theme: 'light' | 'dark' = 'light';
  @Input() readOnly = false;
  @Input() config: EditorConfig = {};

  @Output() contentChange = new EventEmitter<string>();

  private editorView?: EditorView;
  private vimModeCleanup?: () => void;
  private activeKeymap: 'default' | 'vim' | null = null;

  readonly editorService = inject(EditorService);
  readonly editorPrefs = inject(EditorPreferencesService);

  readonly vimModeLabel = signal<VimModeLabel | null>(null);

  constructor() {
    effect(() => {
      const keymap = this.editorPrefs.keymap();
      if (!this.editorView || this.activeKeymap === keymap) {
        return;
      }
      this.activeKeymap = keymap;
      this.editorService.setKeymapMode(this.editorView, keymap);
      this.bindVimModeListener(keymap);
    });
  }

  ngAfterViewInit(): void {
    this.initializeEditor();
  }

  ngOnDestroy(): void {
    this.vimModeCleanup?.();
    if (this.editorView) {
      this.editorService.destroyEditor(this.editorView);
    }
  }

  private initializeEditor(): void {
    const config: EditorConfig = {
      language: this.language,
      theme: this.theme,
      readOnly: this.readOnly,
      keymap: this.editorPrefs.keymap(),
      ...this.config,
    };

    this.editorView = this.editorService.createEditor(
      this.editorContainer.nativeElement,
      config,
      (content) => this.contentChange.emit(content)
    );

    this.activeKeymap = this.editorPrefs.keymap();

    if (this.content) {
      this.editorService.setContent(this.editorView, this.content);
    }

    this.bindVimModeListener(this.editorPrefs.keymap());
  }

  private bindVimModeListener(keymap: 'default' | 'vim'): void {
    this.vimModeCleanup?.();
    if (!this.editorView) {
      this.vimModeLabel.set(null);
      return;
    }

    this.vimModeCleanup = this.editorService.onVimModeChange(
      this.editorView,
      keymap,
      (mode) => {
        this.vimModeLabel.set(mode ? (mode.toUpperCase() as VimModeLabel) : null);
      },
    );
  }

  applyFormat(action: FormatAction): void {
    if (this.editorView && !this.readOnly) {
      this.editorService.applyFormat(this.editorView, action);
    }
  }

  insertAtCursor(text: string): void {
    if (this.editorView && !this.readOnly) {
      this.editorService.insertText(this.editorView, text);
    }
  }

  setContent(content: string): void {
    if (this.editorView) {
      this.editorService.setContent(this.editorView, content);
    }
  }

  getContent(): string {
    return this.editorView
      ? this.editorService.getContent(this.editorView)
      : '';
  }

  setLanguage(language: string): void {
    if (this.editorView) {
      this.editorService.setLanguage(this.editorView, language);
    }
  }

  setTheme(theme: 'light' | 'dark'): void {
    if (this.editorView) {
      this.editorService.setTheme(this.editorView, theme);
    }
  }
}
