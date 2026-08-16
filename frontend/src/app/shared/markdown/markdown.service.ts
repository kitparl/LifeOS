import { Injectable } from '@angular/core';
import DOMPurify from 'dompurify';
import { marked } from 'marked';

/**
 * MarkdownService — single source of truth for converting Markdown to safe HTML.
 *
 * Reusable across Journal, Knowledge Notes, and any future content surface.
 * Rendering is synchronous and the output is sanitized with DOMPurify so it can
 * be bound with [innerHTML] safely.
 */
@Injectable({ providedIn: 'root' })
export class MarkdownService {
  constructor() {
    marked.setOptions({
      gfm: true,
      breaks: true,
    });
  }

  /** Convert a Markdown string into sanitized HTML. */
  render(markdown: string | null | undefined): string {
    if (!markdown) return '';
    const rawHtml = marked.parse(markdown, { async: false }) as string;
    return this.sanitize(rawHtml);
  }

  /** Sanitize rendered HTML before binding with [innerHTML]. */
  sanitize(html: string): string {
    return DOMPurify.sanitize(html, {
      ADD_ATTR: ['target', 'rel'],
      ALLOWED_URI_REGEXP:
        /^(?:(?:https?|mailto|tel|data):|[^a-z]|[a-z+.-]+(?:[^a-z+.:-]|$))/i,
    });
  }

  /** Best-effort plain-text preview for list rows (strips Markdown syntax). */
  toPlainText(markdown: string | null | undefined, maxLength = 160): string {
    if (!markdown) return '';
    const text = markdown
      .replace(/```[\s\S]*?```/g, ' ')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
      .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
      .replace(/[#>*_~`-]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
    return text.length > maxLength ? `${text.slice(0, maxLength).trimEnd()}…` : text;
  }
}
