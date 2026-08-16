import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  ElementRef,
  ViewChild,
  AfterViewInit
} from '@angular/core';
import { EditorView } from 'codemirror';
import { EditorService } from '../../services/editor.service';
import { EditorConfig } from '../../models';
import { FormatAction } from '../editor-toolbar/editor-toolbar.component';

@Component({
  selector: 'app-markdown-editor',
  standalone: true,
  template: `
    <div #editorContainer class="editor-container" [class.read-only]="readOnly"></div>
  `,
  styles: [`
    .editor-container {
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
  `]
})
export class MarkdownEditorComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('editorContainer', { static: true }) editorContainer!: ElementRef<HTMLElement>;

  @Input() content = '';
  @Input() language = 'markdown';
  @Input() theme: 'light' | 'dark' = 'light';
  @Input() readOnly = false;
  @Input() config: EditorConfig = {};

  @Output() contentChange = new EventEmitter<string>();

  private editorView?: EditorView;

  constructor(
    private editorService: EditorService
  ) {}

  ngOnInit(): void {}

  ngAfterViewInit(): void {
    this.initializeEditor();
  }

  ngOnDestroy(): void {
    if (this.editorView) {
      this.editorService.destroyEditor(this.editorView);
    }
  }

  private initializeEditor(): void {
    const config: EditorConfig = {
      language: this.language,
      theme: this.theme,
      readOnly: this.readOnly,
      ...this.config
    };

    this.editorView = this.editorService.createEditor(
      this.editorContainer.nativeElement,
      config,
      (content) => this.contentChange.emit(content)
    );

    if (this.content) {
      this.editorService.setContent(this.editorView, this.content);
    }
  }

  applyFormat(action: FormatAction): void {
    if (this.editorView && !this.readOnly) {
      this.editorService.applyFormat(this.editorView, action);
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
