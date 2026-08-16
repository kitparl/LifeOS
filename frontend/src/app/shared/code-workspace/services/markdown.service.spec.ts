import { TestBed } from '@angular/core/testing';
import { MarkdownService } from './markdown.service';

describe('MarkdownService', () => {
  let service: MarkdownService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MarkdownService);
  });

  it('parses headings, emphasis, and lists', () => {
    const html = service.parse('# Title\n\n**bold** and *italic*\n\n- item');
    expect(html).toContain('<h1');
    expect(html).toContain('<strong>bold</strong>');
    expect(html).toContain('<em>italic</em>');
    expect(html).toContain('<li>');
  });

  it('sanitizes script tags, event handlers, and javascript URLs', () => {
    const dirty = '<p onclick="alert(1)">x</p><script>alert(1)</script><a href="javascript:alert(1)">x</a><img src=x onerror="alert(1)">';
    const clean = service.sanitize(dirty);
    expect(clean.toLowerCase()).not.toContain('<script');
    expect(clean.toLowerCase()).not.toContain('onclick');
    expect(clean.toLowerCase()).not.toContain('onerror');
    expect(clean.toLowerCase()).not.toContain('javascript:');
  });

  it('sanitizes malicious SVG', () => {
    const clean = service.sanitize('<svg onload="alert(1)"><script>alert(1)</script></svg>');
    expect(clean.toLowerCase()).not.toContain('onload');
    expect(clean.toLowerCase()).not.toContain('<script');
  });

  it('handles malformed markdown without throwing', () => {
    expect(() => service.parse('```\nunterminated')).not.toThrow();
    expect(service.parse('')).toBe('');
  });
});
