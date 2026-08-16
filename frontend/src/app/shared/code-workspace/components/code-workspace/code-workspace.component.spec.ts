import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { BreakpointObserver } from '@angular/cdk/layout';
import { of } from 'rxjs';
import { CodeWorkspaceComponent } from './code-workspace.component';
import { CodeExecutionService } from '../../services/code-execution.service';

describe('CodeWorkspaceComponent', () => {
  let fixture: ComponentFixture<CodeWorkspaceComponent>;
  let component: CodeWorkspaceComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CodeWorkspaceComponent],
      providers: [
        provideHttpClient(),
        {
          provide: BreakpointObserver,
          useValue: {
            observe: () => of({ breakpoints: {}, matches: true }),
          },
        },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(CodeWorkspaceComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('content', '# Hi');
    fixture.componentRef.setInput('showLanguageSelector', false);
    fixture.componentRef.setInput('showRunButton', false);
    fixture.detectChanges();
  });

  afterEach(() => fixture.destroy());

  it('exposes a labeled region and accepts configuration inputs', () => {
    expect(fixture.nativeElement.getAttribute('role')).toBe('region');
    expect(fixture.nativeElement.getAttribute('aria-label')).toBe('Code workspace');
    fixture.componentRef.setInput('mode', 'code');
    fixture.componentRef.setInput('showPreview', false);
    fixture.detectChanges();
    expect(component.mode).toBe('code');
    expect(component.showPreview).toBeFalse();
  });

  it('updates stats immediately and emits contentChange', () => {
    const local = TestBed.createComponent(CodeWorkspaceComponent);
    const cmp = local.componentInstance;
    local.detectChanges();
    const values: string[] = [];
    cmp.contentChange.subscribe((v) => values.push(v));
    cmp.onContentChange('hello world');
    expect(values).toEqual(['hello world']);
    expect(cmp.editorStats.wordCount).toBe(2);
    expect(cmp.editorStats.charCount).toBe(11);
    expect(cmp.editorStats.lineCount).toBe(1);
    local.destroy();
  });

  it('emits save documents', () => {
    const saved: string[] = [];
    component.save.subscribe((d) => saved.push(d.content));
    component.onContentChange('saved');
    component.onSave();
    expect(saved).toContain('saved');
  });

  it('replaces document content when the input changes', () => {
    component.currentContent = 'previous note';
    fixture.componentRef.setInput('content', '');
    fixture.detectChanges();
    expect(component.currentContent).toBe('');
  });

  it('emits run and shows output for javascript', fakeAsync(() => {
    const execution = TestBed.inject(CodeExecutionService);
    spyOn(execution, 'isExecutionSupported').and.returnValue(true);
    spyOn(execution, 'execute').and.returnValue(
      of({ success: true, stdout: '1', stderr: '', exitCode: 0 })
    );
    const runs: string[] = [];
    component.run.subscribe((r) => runs.push(r.language));
    fixture.componentRef.setInput('showRunButton', true);
    fixture.componentRef.setInput('language', 'javascript');
    component.currentLanguage = 'javascript';
    component.currentContent = 'console.log(1)';
    component.onRunCode();
    tick();
    expect(runs).toContain('javascript');
    expect(component.executionResult?.stdout).toBe('1');
  }));

  it('defaults to write on wide layout; split only after Preview', () => {
    component.isMobile = false;
    component.isTablet = false;
    component.isDesktop = true;
    fixture.componentRef.setInput('showPreview', true);
    expect(component.viewMode).toBe('write');
    expect(component.splitOrientation).toBe('horizontal');
    expect(component.shouldShowSplitView()).toBeFalse();
    expect(component.shouldShowEditor()).toBeTrue();
    expect(component.shouldShowPreview()).toBeFalse();
    expect(component.shouldShowViewModes()).toBeTrue();

    component.onViewModeChange('split');
    expect(component.shouldShowSplitView()).toBeTrue();
    expect(component.splitOrientation).toBe('horizontal');
    expect(component.shouldShowEditor()).toBeTrue();
    expect(component.shouldShowPreview()).toBeTrue();

    component.onSplitOrientationChange('vertical');
    expect(component.splitOrientation).toBe('vertical');
    expect(component.shouldShowSplitView()).toBeTrue();
    expect(component.splitRatio).toBe(0.5);

    component.onViewModeChange('write');
    expect(component.shouldShowSplitView()).toBeFalse();
    expect(component.shouldShowPreview()).toBeFalse();
  });

  it('hides the editor in preview-only mode', () => {
    component.isMobile = false;
    fixture.componentRef.setInput('showPreview', true);
    component.onViewModeChange('preview');
    expect(component.shouldShowEditor()).toBeFalse();
    expect(component.shouldShowPreview()).toBeTrue();
    expect(component.shouldShowSplitView()).toBeFalse();
  });

  it('treats tablet like desktop so preview is reachable', () => {
    component.isMobile = false;
    component.isTablet = true;
    component.isDesktop = false;
    fixture.componentRef.setInput('showPreview', true);
    expect(component.shouldShowTabs()).toBeFalse();
    expect(component.shouldShowViewModes()).toBeTrue();
    expect(component.shouldShowSplitView()).toBeFalse();
    component.onViewModeChange('split');
    expect(component.shouldShowSplitView()).toBeTrue();
    expect(component.shouldShowPreview()).toBeTrue();
  });

  it('keeps mobile tabs and does not force split', () => {
    component.isMobile = true;
    component.currentView = 'edit';
    fixture.componentRef.setInput('showPreview', true);
    expect(component.shouldShowTabs()).toBeTrue();
    expect(component.shouldShowSplitView()).toBeFalse();
    expect(component.shouldShowViewModes()).toBeFalse();
    expect(component.shouldShowEditor()).toBeTrue();
    expect(component.shouldShowPreview()).toBeFalse();
    component.currentView = 'preview';
    expect(component.shouldShowPreview()).toBeTrue();
    expect(component.shouldShowEditor()).toBeFalse();
  });

  it('defaults the editor/preview split to 50/50 and lets it be resized', () => {
    expect(component.splitRatio).toBe(0.5);
    expect(component.splitPercent).toBe(50);

    component.updateSplitFromPointer(300, 0, 400);
    expect(component.splitRatio).toBe(0.75);

    component.updateSplitFromPointer(10, 0, 400);
    expect(component.splitRatio).toBe(0.2);

    component.updateSplitFromPointer(390, 0, 400);
    expect(component.splitRatio).toBe(0.8);

    component.resetSplitRatio();
    expect(component.splitRatio).toBe(0.5);

    component.splitRatio = 0.5;
    component.onResizeKeydown(new KeyboardEvent('keydown', { key: 'ArrowRight' }));
    expect(component.splitRatio).toBeCloseTo(0.55);
    component.onResizeKeydown(new KeyboardEvent('keydown', { key: 'Home' }));
    expect(component.splitRatio).toBe(0.5);
  });

  it('clears execution output when the panel emits cleared', () => {
    component.executionResult = { success: true, stdout: '1', stderr: '', exitCode: 0 };
    component.onOutputCleared();
    expect(component.executionResult).toBeNull();
  });

  it('fills the parent height', () => {
    const css = (
      CodeWorkspaceComponent as unknown as { ɵcmp: { styles: string[] } }
    ).ɵcmp?.styles?.join(' ') || '';
    expect(css).toContain('height: 100%');
    expect(css).toContain('min-height: 0');
  });

  it('covers the viewport in fullscreen and exits on Escape', () => {
    const css = (
      CodeWorkspaceComponent as unknown as { ɵcmp: { styles: string[] } }
    ).ɵcmp?.styles?.join(' ') || '';
    expect(css).toContain('position: fixed');
    expect(css).toContain('inset: 0');

    expect(component.fullscreen).toBeFalse();
    component.toggleFullscreen();
    expect(component.fullscreen).toBeTrue();
    expect(component.viewMode).toBe('write');
    component.onViewModeChange('split');
    component.onEscape(new KeyboardEvent('keydown', { key: 'Escape' }));
    expect(component.fullscreen).toBeFalse();
    expect(component.viewMode).toBe('split');
  });

  it('does not steal Escape from an open dialog', () => {
    component.toggleFullscreen();
    const dialog = document.createElement('div');
    dialog.setAttribute('role', 'dialog');
    document.body.appendChild(dialog);
    component.onEscape(new KeyboardEvent('keydown', { key: 'Escape' }));
    expect(component.fullscreen).toBeTrue();
    dialog.remove();
  });

  it('emits filesPasted when enableFilePaste and paste contains files', () => {
    fixture.componentRef.setInput('enableFilePaste', true);
    fixture.detectChanges();
    const emitted: File[][] = [];
    component.filesPasted.subscribe((files) => emitted.push(files));
    const file = new File(['x'], 'a.png', { type: 'image/png' });
    const event = {
      clipboardData: {
        items: [{ kind: 'file', getAsFile: () => file }],
        files: [file],
      },
      preventDefault: jasmine.createSpy('preventDefault'),
      stopPropagation: jasmine.createSpy('stopPropagation'),
    } as unknown as ClipboardEvent;
    component.onEditorPaste(event);
    expect(emitted.length).toBe(1);
    expect(emitted[0][0].name).toBe('a.png');
    expect(event.preventDefault).toHaveBeenCalled();
  });

  it('does not intercept paste when enableFilePaste is false', () => {
    const emitted: File[][] = [];
    component.filesPasted.subscribe((files) => emitted.push(files));
    const file = new File(['x'], 'a.png', { type: 'image/png' });
    const event = {
      clipboardData: {
        items: [{ kind: 'file', getAsFile: () => file }],
        files: [file],
      },
      preventDefault: jasmine.createSpy('preventDefault'),
      stopPropagation: jasmine.createSpy('stopPropagation'),
    } as unknown as ClipboardEvent;
    component.onEditorPaste(event);
    expect(emitted.length).toBe(0);
    expect(event.preventDefault).not.toHaveBeenCalled();
  });
});
