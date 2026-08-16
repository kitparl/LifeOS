import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MarkdownPreviewComponent } from './markdown-preview.component';

describe('MarkdownPreviewComponent', () => {
  let fixture: ComponentFixture<MarkdownPreviewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarkdownPreviewComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(MarkdownPreviewComponent);
  });

  it('renders markdown to sanitized HTML immediately', () => {
    fixture.componentRef.setInput('content', '# Hello <script>alert(1)</script>');
    fixture.detectChanges();
    const html = fixture.nativeElement.innerHTML as string;
    expect(html).toContain('Hello');
    expect(html.toLowerCase()).not.toContain('<script');
    expect(fixture.nativeElement.querySelector('[role="article"]')).toBeTruthy();
  });

  it('emits ul/li for markdown bullets', () => {
    fixture.componentRef.setInput('content', '- one\n- two');
    fixture.detectChanges();
    const html = fixture.nativeElement.innerHTML as string;
    expect(html).toContain('<ul');
    expect(html).toContain('<li>');
  });
});
