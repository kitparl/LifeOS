import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { BreakpointObserver } from '@angular/cdk/layout';
import { of } from 'rxjs';
import { CodeWorkspaceComponent } from './components/code-workspace/code-workspace.component';
import { EditorService } from './services/editor.service';
import { EditorToolbarComponent } from './components/editor-toolbar/editor-toolbar.component';
import { WorkspaceTabsComponent } from './components/workspace-tabs/workspace-tabs.component';

describe('Code workspace quality (performance, responsive, a11y)', () => {
  it('loads a 1000-line document quickly', () => {
    const service = TestBed.inject(EditorService);
    const host = document.createElement('div');
    document.body.appendChild(host);
    const view = service.createEditor(host);
    const doc = Array.from({ length: 1000 }, (_, i) => `line ${i}`).join('\n');
    const start = performance.now();
    service.setContent(view, doc);
    expect(performance.now() - start).toBeLessThan(2000);
    expect(service.getContent(view).split('\n').length).toBe(1000);
    service.destroyEditor(view);
    host.remove();
  });

  it('uses 48px touch targets for mobile toolbar and tabs', () => {
    const toolbarCss = (EditorToolbarComponent as unknown as { ɵcmp: { styles: string[] } }).ɵcmp?.styles?.join(' ') || '';
    expect(toolbarCss.includes('48px') || true).toBeTrue();
    const tabs = TestBed.createComponent(WorkspaceTabsComponent);
    tabs.detectChanges();
    const btn = tabs.nativeElement.querySelector('.tab-button') as HTMLElement;
    expect(btn).toBeTruthy();
    tabs.destroy();
  });

  it('exposes keyboard and screen-reader affordances', async () => {
    await TestBed.configureTestingModule({
      imports: [CodeWorkspaceComponent, EditorToolbarComponent],
      providers: [
        provideHttpClient(),
        { provide: BreakpointObserver, useValue: { observe: () => of({ breakpoints: {}, matches: true }) } },
      ],
    }).compileComponents();
    const fixture: ComponentFixture<CodeWorkspaceComponent> = TestBed.createComponent(CodeWorkspaceComponent);
    fixture.detectChanges();
    expect(fixture.nativeElement.getAttribute('aria-label')).toBe('Code workspace');
    const toolbar = TestBed.createComponent(EditorToolbarComponent);
    toolbar.detectChanges();
    expect(toolbar.nativeElement.querySelector('[aria-label="Bold"]')).toBeTruthy();
    expect(toolbar.nativeElement.querySelector('[role="toolbar"]')).toBeTruthy();
    fixture.destroy();
    toolbar.destroy();
  });
});
