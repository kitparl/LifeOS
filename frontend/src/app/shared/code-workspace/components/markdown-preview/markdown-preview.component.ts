import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
} from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { CommonModule } from '@angular/common';
import { MarkdownService } from '../../services/markdown.service';
import { FileImageSrcDirective } from '../../../markdown/file-image-src.directive';
import { RunnableFencesDirective } from '../../directives/runnable-fences.directive';
import { ParsedCodeBlock } from '../../utils/fenced-code-blocks';

@Component({
  selector: 'app-markdown-preview',
  standalone: true,
  imports: [CommonModule, FileImageSrcDirective, RunnableFencesDirective],
  template: `
    <div
      class="markdown-preview-container markdown-body"
      role="article"
      aria-label="Markdown preview"
      appFileImageSrc
      [appRunnableFences]="runnableBlocks"
      [runningFenceId]="runningBlockId"
      [fenceRunDisabled]="runDisabled"
      (fenceRun)="runBlock.emit($event)"
      [class.theme-light]="theme === 'light'"
      [class.theme-dark]="theme === 'dark'"
      [class.journal-reader]="variant === 'journal'"
      [innerHTML]="renderedContent"
    ></div>
  `,
  styles: [`
    .markdown-preview-container {
      padding: 1rem 1.25rem;
      overflow-y: auto;
      height: 100%;
      width: 100%;
      word-wrap: break-word;
      overflow-wrap: break-word;
      background: var(--surface);
      color: var(--text);
    }

    .markdown-preview-container.journal-reader {
      padding: 1.75rem 1.5rem 2.5rem;
      max-width: 42rem;
      margin: 0 auto;
    }

    .markdown-preview-container :deep(img) {
      max-width: 100%;
      height: auto;
    }

    :host {
      display: block;
      height: 100%;
      width: 100%;
    }
  `]
})
export class MarkdownPreviewComponent implements OnChanges {
  @Input() content = '';
  @Input() theme: 'light' | 'dark' | 'system' = 'light';
  @Input() variant: 'default' | 'journal' = 'default';
  /** Executable fences to decorate with an inline Run button (opt-in). */
  @Input() runnableBlocks: ParsedCodeBlock[] = [];
  @Input() runningBlockId: string | null = null;
  @Input() runDisabled = false;

  @Output() runBlock = new EventEmitter<ParsedCodeBlock>();

  renderedContent: SafeHtml = '';

  constructor(
    private markdownService: MarkdownService,
    private domSanitizer: DomSanitizer
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['content'] || (changes['theme'] && !changes['theme'].firstChange)) {
      this.renderContent(this.content);
    }
  }

  private renderContent(markdown: string): void {
    if (!markdown || markdown.trim() === '') {
      this.renderedContent = '';
      return;
    }

    try {
      const html = this.markdownService.parse(markdown);
      const sanitized = this.markdownService.sanitize(html);
      this.renderedContent = this.domSanitizer.bypassSecurityTrustHtml(sanitized);
    } catch (error) {
      console.error('Error rendering markdown preview:', error);
      this.renderedContent = '<p>Error rendering preview</p>';
    }
  }
}
