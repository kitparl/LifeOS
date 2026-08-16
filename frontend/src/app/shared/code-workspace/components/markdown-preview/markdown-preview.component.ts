import {
  Component,
  Input,
  OnChanges,
  SimpleChanges,
} from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { CommonModule } from '@angular/common';
import { MarkdownService } from '../../services/markdown.service';

@Component({
  selector: 'app-markdown-preview',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="markdown-preview-container markdown-body"
      role="article"
      aria-label="Markdown preview"
      [class.theme-light]="theme === 'light'"
      [class.theme-dark]="theme === 'dark'"
      [innerHTML]="renderedContent"
    ></div>
  `,
  styles: [`
    .markdown-preview-container {
      padding: 1rem;
      overflow-y: auto;
      height: 100%;
      width: 100%;
      word-wrap: break-word;
      overflow-wrap: break-word;
      background: var(--surface);
      color: var(--text);
    }

    /* Markdown styling */
    .markdown-preview-container :deep(h1) {
      font-size: 2em;
      font-weight: bold;
      margin-top: 0.67em;
      margin-bottom: 0.67em;
    }

    .markdown-preview-container :deep(h2) {
      font-size: 1.5em;
      font-weight: bold;
      margin-top: 0.83em;
      margin-bottom: 0.83em;
    }

    .markdown-preview-container :deep(h3) {
      font-size: 1.17em;
      font-weight: bold;
      margin-top: 1em;
      margin-bottom: 1em;
    }

    .markdown-preview-container :deep(p) {
      margin: 1em 0;
    }

    .markdown-preview-container :deep(ul),
    .markdown-preview-container :deep(ol) {
      margin: 1em 0;
      padding-left: 2em;
    }

    .markdown-preview-container :deep(ul) {
      list-style-type: disc;
      list-style-position: outside;
    }

    .markdown-preview-container :deep(ol) {
      list-style-type: decimal;
      list-style-position: outside;
    }

    .markdown-preview-container :deep(ul ul) {
      list-style-type: circle;
    }

    .markdown-preview-container :deep(ul ul ul) {
      list-style-type: square;
    }

    .markdown-preview-container :deep(li) {
      margin: 0.5em 0;
    }

    .markdown-preview-container :deep(blockquote) {
      border-left: 4px solid #ddd;
      padding-left: 1em;
      margin: 1em 0;
      color: #666;
    }

    .markdown-preview-container :deep(code) {
      background-color: #f5f5f5;
      padding: 0.2em 0.4em;
      border-radius: 3px;
      font-family: 'Courier New', monospace;
    }

    .markdown-preview-container :deep(pre) {
      background-color: #f5f5f5;
      padding: 1em;
      border-radius: 5px;
      overflow-x: auto;
      max-width: 100%;
    }

    .markdown-preview-container :deep(pre code) {
      background-color: transparent;
      padding: 0;
    }

    .markdown-preview-container :deep(img) {
      max-width: 100%;
      height: auto;
    }

    .markdown-preview-container :deep(table) {
      border-collapse: collapse;
      width: 100%;
      overflow-x: auto;
      display: block;
      max-width: 100%;
    }

    .markdown-preview-container :deep(th),
    .markdown-preview-container :deep(td) {
      border: 1px solid #ddd;
      padding: 0.5em;
      text-align: left;
    }

    .markdown-preview-container :deep(th) {
      background-color: #f5f5f5;
      font-weight: bold;
    }

    .markdown-preview-container :deep(hr) {
      border: none;
      border-top: 1px solid #ddd;
      margin: 2em 0;
    }

    .markdown-preview-container :deep(a) {
      color: #0066cc;
      text-decoration: none;
    }

    .markdown-preview-container :deep(a:hover) {
      text-decoration: underline;
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
      // Parse markdown to HTML
      const html = this.markdownService.parse(markdown);
      
      // Sanitize HTML (dual sanitization: DOMPurify + Angular)
      const sanitized = this.markdownService.sanitize(html);
      
      // Bypass Angular sanitization since we've already sanitized
      this.renderedContent = this.domSanitizer.bypassSecurityTrustHtml(sanitized);
    } catch (error) {
      console.error('Error rendering markdown preview:', error);
      this.renderedContent = '<p>Error rendering preview</p>';
    }
  }
}
