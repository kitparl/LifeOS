import { Injectable } from '@angular/core';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

@Injectable({
  providedIn: 'root',
})
export class MarkdownService {
  constructor() {
    marked.setOptions({
      gfm: true,
      breaks: true,
    });

    // Mutates DOMPurify globally — also affects shared/markdown MarkdownService.
    DOMPurify.addHook('afterSanitizeAttributes', (node) => {
      if (node.tagName === 'A' && node.hasAttribute('href')) {
        const href = node.getAttribute('href');
        if (href && href.startsWith('http')) {
          node.setAttribute('target', '_blank');
          node.setAttribute('rel', 'noopener noreferrer');
        }
      }

      if (node.tagName === 'IMG' && node instanceof HTMLElement) {
        node.style.maxWidth = '100%';
        node.style.height = 'auto';
      }
    });
  }

  parse(markdown: string): string {
    try {
      return marked.parse(markdown) as string;
    } catch (error) {
      console.error('Markdown parsing error:', error);
      return '<p>Error parsing markdown</p>';
    }
  }

  sanitize(html: string): string {
    return DOMPurify.sanitize(html, {
      ALLOWED_TAGS: [
        'p', 'br', 'strong', 'em', 'u', 's', 'del', 'ins',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li',
        'blockquote', 'pre', 'code',
        'a', 'img',
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'hr', 'div', 'span',
      ],
      ALLOWED_ATTR: [
        'href', 'src', 'alt', 'title', 'class', 'id',
        'width', 'height', 'align', 'style',
      ],
      ALLOWED_URI_REGEXP:
        /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp):|[^a-z]|[a-z+.-]+(?:[^a-z+.:-]|$))/i,
      KEEP_CONTENT: true,
      RETURN_TRUSTED_TYPE: false,
    });
  }
}
