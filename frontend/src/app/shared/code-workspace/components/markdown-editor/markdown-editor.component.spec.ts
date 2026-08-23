import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { MarkdownEditorComponent } from './markdown-editor.component';
import { EditorPreferencesService } from '../../../../core/services/editor-preferences.service';

describe('MarkdownEditorComponent', () => {
  let fixture: ComponentFixture<MarkdownEditorComponent>;
  let component: MarkdownEditorComponent;
  let editorPrefs: EditorPreferencesService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MarkdownEditorComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    fixture = TestBed.createComponent(MarkdownEditorComponent);
    component = fixture.componentInstance;
    editorPrefs = TestBed.inject(EditorPreferencesService);
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

  it('scrolls inside a bounded host instead of growing with the document', () => {
    const css = (
      MarkdownEditorComponent as unknown as { ɵcmp: { styles: string[] } }
    ).ɵcmp?.styles?.join(' ') || '';
    expect(css).toContain('height: 100%');
    expect(css).toContain('overflow: hidden');
  });

  it('preserves content when switching keymap preference', fakeAsync(() => {
    component.setContent('persisted');
    tick();
    editorPrefs.setKeymap('vim');
    tick();
    expect(component.getContent()).toBe('persisted');
    editorPrefs.setKeymap('default');
    tick();
    expect(component.getContent()).toBe('persisted');
  }));

  it('shows vim mode badge when vim keymap is active', fakeAsync(() => {
    editorPrefs.setKeymap('vim');
    tick();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.vim-mode-badge')).toBeTruthy();
  }));
});
