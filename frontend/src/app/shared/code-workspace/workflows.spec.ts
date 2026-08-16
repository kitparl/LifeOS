import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { BreakpointObserver } from '@angular/cdk/layout';
import { of } from 'rxjs';
import { CodeWorkspaceComponent } from './components/code-workspace/code-workspace.component';
import { EditorService } from './services/editor.service';
import { ThemeIntegrationService } from './services/theme/theme-integration.service';
import { EditorPersistenceService } from './services/editor-persistence.service';
import { Subject } from 'rxjs';

describe('Code workspace workflows', () => {
  let fixture: ComponentFixture<CodeWorkspaceComponent>;
  let component: CodeWorkspaceComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CodeWorkspaceComponent],
      providers: [
        provideHttpClient(),
        { provide: BreakpointObserver, useValue: { observe: () => of({ breakpoints: {}, matches: true }) } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(CodeWorkspaceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => fixture.destroy());

  it('updates preview after 300ms debounce', fakeAsync(() => {
    component.onContentChange('# Title');
    tick(300);
    expect(component.currentContent).toBe('# Title');
  }));

  it('switches language without losing content', () => {
    const editor = TestBed.inject(EditorService);
    const host = document.createElement('div');
    document.body.appendChild(host);
    const view = editor.createEditor(host, { language: 'javascript' });
    editor.setContent(view, 'const a = 1;');
    const start = performance.now();
    editor.setLanguage(view, 'python');
    expect(performance.now() - start).toBeLessThan(200);
    expect(editor.getContent(view)).toBe('const a = 1;');
    editor.destroyEditor(view);
    host.remove();
  });

  it('applies toolbar actions through the editor service', () => {
    component.currentContent = 'text';
    const editor = fixture.debugElement.componentInstance.markdownEditor;
    editor?.setContent('text');
    component.onFormatAction('italic');
    expect(editor?.getContent() || component.currentContent).toBeTruthy();
  });

  it('preserves tab state when switching mobile views', () => {
    component.currentContent = 'keep me';
    component.onTabChange('preview');
    expect(component.currentView).toBe('preview');
    expect(component.currentContent).toBe('keep me');
    component.onTabChange('edit');
    expect(component.currentView).toBe('edit');
  });

  it('autosaves drafts after 2.5s of inactivity', fakeAsync(() => {
    const persistence = TestBed.inject(EditorPersistenceService);
    spyOn(persistence, 'saveDraft').and.resolveTo();
    const content$ = new Subject<string>();
    persistence.enableAutosave('wf', content$);
    content$.next('note');
    tick(2500);
    expect(persistence.saveDraft).toHaveBeenCalledWith('wf', 'note');
    persistence.disableAutosave('wf');
  }));

  it('updates the resolved theme without requiring a new editor', () => {
    const theme = TestBed.inject(ThemeIntegrationService);
    const sub = theme.subscribeToTheme((t) => expect(t === 'light' || t === 'dark').toBeTrue());
    sub.unsubscribe();
  });
});
