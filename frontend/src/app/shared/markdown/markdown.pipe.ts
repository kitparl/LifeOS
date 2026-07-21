import { Pipe, PipeTransform, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { MarkdownService } from './markdown.service';

/**
 * `markdown` pipe — renders a Markdown string to sanitized, trusted HTML.
 *
 * Usage:
 *   <div class="markdown-body" [innerHTML]="entry.content | markdown"></div>
 *
 * The value is sanitized via DOMPurify inside MarkdownService, then marked as
 * trusted so Angular's sanitizer does not strip it a second time.
 */
@Pipe({ name: 'markdown', standalone: true })
export class MarkdownPipe implements PipeTransform {
  private readonly markdown = inject(MarkdownService);
  private readonly sanitizer = inject(DomSanitizer);

  transform(value: string | null | undefined): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(this.markdown.render(value));
  }
}
