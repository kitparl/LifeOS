import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { MarkdownEditorComponent } from './markdown-editor.component';

describe('MarkdownEditorComponent', () => {
  let fixture: ComponentFixture<MarkdownEditorComponent>;
  let component: MarkdownEditorComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarkdownEditorComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(MarkdownEditorComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('content', 'hello');
    fixture.detectChanges();
  });

  afterEach(() => {
    fixture.destroy();
  });

  it('edits content and emits changes', fakeAsync(() => {
    const emitted: string[] = [];
    component.contentChange.subscribe((c) => emitted.push(c));
    component.setContent('world');
    tick();
    expect(component.getContent()).toBe('world');
    expect(emitted).toContain('world');
  }));

  it('applies format actions', () => {
    component.setContent('hi');
    component.applyFormat('bold');
    expect(component.getContent()).toContain('**');
  });
});
