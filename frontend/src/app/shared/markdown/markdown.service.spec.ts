import { TestBed } from '@angular/core/testing';
import { MarkdownService } from './markdown.service';

describe('MarkdownService (shared render)', () => {
  let service: MarkdownService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MarkdownService);
  });

  it('emits ul/li for dash bullets and ol/li for numbered lists', () => {
    const bullets = service.render('- one\n- two');
    expect(bullets).toContain('<ul');
    expect(bullets).toContain('<li>');
    expect(bullets).toContain('one');

    const nested = service.render('- parent\n  - child');
    expect(nested).toContain('<ul');
    expect((nested.match(/<ul/g) || []).length).toBeGreaterThan(1);

    const numbered = service.render('1. two');
    expect(numbered).toContain('<ol');
    expect(numbered).toContain('<li>');
    expect(numbered).toContain('two');
  });
});
