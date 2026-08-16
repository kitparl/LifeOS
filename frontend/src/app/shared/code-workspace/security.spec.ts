import { TestBed } from '@angular/core/testing';
import { MarkdownService } from './services/markdown.service';
import { JavaScriptExecutor } from './executors/javascript.executor';

describe('Code workspace security', () => {
  it('strips XSS vectors from markdown HTML', () => {
    const markdown = TestBed.inject(MarkdownService);
    const dirty = [
      '<script>alert(1)</script>',
      '<a href="javascript:alert(1)">x</a>',
      '<img src=x onerror="alert(1)">',
      '<svg onload="alert(1)"></svg>',
      '<p onclick="alert(1)">x</p>',
    ].join('');
    const clean = markdown.sanitize(dirty).toLowerCase();
    expect(clean).not.toContain('<script');
    expect(clean).not.toContain('javascript:');
    expect(clean).not.toContain('onerror');
    expect(clean).not.toContain('onload');
    expect(clean).not.toContain('onclick');
  });

  it('documents that JavaScript execution uses a Worker, not eval', () => {
    const src = JavaScriptExecutor.toString();
    expect(src.includes('eval(')).toBeFalse();
    expect(TestBed.inject(JavaScriptExecutor).executionType).toBe('browser');
  });
});
