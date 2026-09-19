import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { DevToolShellComponent } from '../../shared/dev-tool-shell.component';
import { CopyButtonComponent } from '../../shared/copy-button.component';

const DEFAULT_MARKDOWN = '# Hello\n\nThis is **Markdown**. Edit the text on the left.\n\n- item one\n- item two';

@Component({
  selector: 'app-markdown-preview-tool',
  standalone: true,
  imports: [FormsModule, DevToolShellComponent, CopyButtonComponent],
  template: `
    <app-dev-tool-shell
      toolId="markdown-preview"
      title="Markdown Preview"
      description="Preview Markdown and view the generated (sanitized) HTML source."
      icon="file-type"
    >
      <div class="flex justify-end gap-2 pb-3">
        <div class="inline-flex overflow-hidden rounded-[var(--radius-sm)] border border-[var(--border)]">
          <button type="button" class="px-3 py-1.5 text-sm" [style.background]="view() === 'preview' ? 'var(--primary)' : 'transparent'" [style.color]="view() === 'preview' ? '#fff' : 'var(--text)'" (click)="view.set('preview')">Preview</button>
          <button type="button" class="px-3 py-1.5 text-sm border-l border-[var(--border)]" [style.background]="view() === 'html' ? 'var(--primary)' : 'transparent'" [style.color]="view() === 'html' ? '#fff' : 'var(--text)'" (click)="view.set('html')">HTML source</button>
        </div>
        @if (view() === 'html') {
          <app-copy-button [text]="html()" />
        }
      </div>
      <div class="grid gap-3 md:grid-cols-2">
        <div class="space-y-1">
          <label class="form-label">Markdown</label>
          <textarea class="input-field h-72 resize-y font-mono text-sm" [ngModel]="markdownText()" (ngModelChange)="markdownText.set($event)"></textarea>
        </div>
        <div class="space-y-1">
          <label class="form-label">{{ view() === 'preview' ? 'Preview' : 'HTML source' }}</label>
          @if (view() === 'preview') {
            <div class="input-field h-72 overflow-auto text-sm" [innerHTML]="html()"></div>
          } @else {
            <pre class="input-field h-72 overflow-auto whitespace-pre-wrap font-mono text-xs">{{ html() }}</pre>
          }
        </div>
      </div>
    </app-dev-tool-shell>
  `,
})
export class MarkdownPreviewToolComponent {
  readonly markdownText = signal(DEFAULT_MARKDOWN);
  readonly view = signal<'preview' | 'html'>('preview');

  readonly html = computed(() => DOMPurify.sanitize(marked.parse(this.markdownText(), { async: false }) as string));
}
