import { Injectable } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

@Injectable({
  providedIn: 'root'
})
export class MarkdownService {
  constructor(private domSanitizer: DomSanitizer) {
    this.configureMarked();
    this.configureDOMPurify();
  }

  /**
   * Parse Markdown to HTML
   */
  parse(markdown: string): string {
    try {
      return marked.parse(markdown) as string;
    } catch (error) {
      console.error('Markdown parsing error:', error);
      return '<p>Error parsing markdown</p>';
    }
  }

  /**
   * Sanitize HTML using dual sanitization (DOMPurify + Angular)
   */
  sanitize(html: string): string {
    // First layer: DOMPurify
    const purified = DOMPurify.sanitize(html, {
      ALLOWED_TAGS: [
        'p', 'br', 'strong', 'em', 'u', 's', 'del', 'ins',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li',
        'blockquote', 'pre', 'code',
        'a', 'img',
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'hr', 'div', 'span'
      ],
      ALLOWED_ATTR: [
        'href', 'src', 'alt', 'title', 'class', 'id',
        'width', 'height', 'align', 'style'
      ],
      ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i,
      KEEP_CONTENT: true,
      RETURN_TRUSTED_TYPE: false
    });

    return purified;
  }

  /**
   * Render Markdown with full sanitization pipeline
   */
  renderPreview(markdown: string): SafeHtml {
    const html = this.parse(markdown);
    const sanitized = this.sanitize(html);
    
    // Second layer: Angular DomSanitizer
    return this.domSanitizer.sanitize(1, sanitized) || '';
  }

  /**
   * Highlight code blocks (for fenced code blocks in Markdown preview)
   */
  highlightCode(code: string, language: string): string {
    // For now, return code wrapped in pre/code tags
    // Can integrate highlight.js or prism.js later
    const escapedCode = this.escapeHtml(code);
    return `<pre><code class="language-${language}">${escapedCode}</code></pre>`;
  }

  /**
   * Extract frontmatter from Markdown (optional feature)
   */
  extractFrontmatter(markdown: string): { frontmatter: any; content: string } {
    const frontmatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/;
    const match = markdown.match(frontmatterRegex);

    if (match) {
      try {
        const frontmatter = this.parseFrontmatter(match[1]);
        return { frontmatter, content: match[2] };
      } catch {
        return { frontmatter: {}, content: markdown };
      }
    }

    return { frontmatter: {}, content: markdown };
  }

  private configureMarked(): void {
  marked.setOptions({
      gfm: true,
      breaks: true,
    });
  }

  private configureDOMPurify(): void {
    // Add hooks to DOMPurify if needed
    DOMPurify.addHook('afterSanitizeAttributes', (node) => {
      // Ensure external links open in new tab
      if (node.tagName === 'A' && node.hasAttribute('href')) {
        const href = node.getAttribute('href');
        if (href && href.startsWith('http')) {
          node.setAttribute('target', '_blank');
          node.setAttribute('rel', 'noopener noreferrer');
        }
      }

      // Make images responsive
      if (node.tagName === 'IMG' && node instanceof HTMLElement) {
        node.style.maxWidth = '100%';
        node.style.height = 'auto';
      }
    });
  }

  private parseFrontmatter(frontmatter: string): any {
    const lines = frontmatter.split('\n');
    const result: any = {};

    lines.forEach(line => {
      const match = line.match(/^(\w+):\s*(.+)$/);
      if (match) {
        result[match[1]] = match[2];
      }
    });

    return result;
  }

  private escapeHtml(html: string): string {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
  }
}
