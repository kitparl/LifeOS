import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { MarkdownPreviewComponent } from './markdown-preview.component';

describe('MarkdownPreviewComponent', () => {
  let fixture: ComponentFixture<MarkdownPreviewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarkdownPreviewComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(MarkdownPreviewComponent);
  });

  it('renders markdown to sanitized HTML after debounce', fakeAsync(() => {
    fixture.componentRef.setInput('content', '# Hello <script>alert(1)</script>');
    fixture.componentRef.setInput('debounceTime', 300);
    fixture.detectChanges();
    tick(300);
    fixture.detectChanges();
    const html = fixture.nativeElement.innerHTML as string;
    expect(html).toContain('Hello');
    expect(html.toLowerCase()).not.toContain('<script');
    expect(fixture.nativeElement.querySelector('[role="article"]')).toBeTruthy();
  }));
});
