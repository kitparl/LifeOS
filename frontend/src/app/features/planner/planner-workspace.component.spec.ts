import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConfirmService } from '../../shared/confirm/confirm.service';
import { NAV_LUCIDE_ICON_PROVIDERS } from '../../shared/layout/nav-lucide';
import { PlannerExplorerComponent } from './components/planner-explorer.component';
import { DrawioEditorComponent } from './components/drawio-editor.component';
import { PlannerNode } from './models/planner.models';
import { PlannerApiService } from './services/planner-api.service';
import { PlannerTreeStore } from './services/planner-tree.store';
import { PlannerWorkspaceComponent } from './planner-workspace.component';

const STORAGE_KEY = 'lifeos.planner.tabs';
const EXPLORER_KEY = 'lifeos.planner.explorer';

function node(id: string, kind: PlannerNode['kind'], name = id): PlannerNode {
  return { id, parent_id: null, kind, name, order_index: 0, revision: 1, created_at: '', updated_at: '' };
}

describe('PlannerWorkspaceComponent', () => {
  let fixture: ComponentFixture<PlannerWorkspaceComponent>;
  let nodes: ReturnType<typeof signal<PlannerNode[]>>;
  let loadResolve: () => void;
  let confirm: jasmine.SpyObj<ConfirmService>;

  async function create(stored?: unknown): Promise<PlannerWorkspaceComponent> {
    if (stored) localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
    fixture = TestBed.createComponent(PlannerWorkspaceComponent);
    fixture.detectChanges();
    loadResolve();
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture.componentInstance;
  }

  beforeEach(() => {
    localStorage.removeItem(STORAGE_KEY);
    nodes = signal([node('d1', 'diagram', 'One'), node('d2', 'diagram', 'Two'), node('p', 'project')]);
    const store = {
      nodes,
      filter: signal(''),
      error: signal<string | null>(null),
      expanded: signal(new Set<string>()),
      visibleTree: () => [],
      load: () => new Promise<void>((resolve) => (loadResolve = resolve)),
    };
    confirm = jasmine.createSpyObj('ConfirmService', ['confirm']);
    TestBed.configureTestingModule({
      imports: [PlannerWorkspaceComponent],
      providers: [
        ...NAV_LUCIDE_ICON_PROVIDERS,
        { provide: ConfirmService, useValue: confirm },
        { provide: PlannerApiService, useValue: {} },
      ],
    });
    TestBed.overrideComponent(PlannerWorkspaceComponent, {
      set: { providers: [{ provide: PlannerTreeStore, useValue: store }] },
    });
    TestBed.overrideComponent(PlannerExplorerComponent, { set: { template: '' } });
    TestBed.overrideComponent(DrawioEditorComponent, { set: { template: '' } });
  });

  afterEach(() => localStorage.removeItem(STORAGE_KEY));

  it('shows the empty state when no tabs are open', async () => {
    await create();
    expect(fixture.nativeElement.textContent).toContain('Open a diagram from the explorer');
  });

  it('drops restored tab ids that are not diagrams in the store, after load', async () => {
    const page = await create({ open: ['d1', 'gone', 'p'], active: 'gone' });
    expect(page.openTabs()).toEqual(['d1']);
    expect(page.activeTab()).toBe('d1');
  });

  it('closes removed tabs without prompting and persists', async () => {
    const page = await create({ open: ['d1', 'd2'], active: 'd1' });
    page.closeRemoved(['d1']);
    expect(page.openTabs()).toEqual(['d2']);
    expect(page.activeTab()).toBe('d2');
    expect(JSON.parse(localStorage.getItem(STORAGE_KEY)!)).toEqual({ open: ['d2'], active: 'd2' });
    expect(confirm.confirm).not.toHaveBeenCalled();
  });

  it('opens a diagram once and activates it', async () => {
    const page = await create();
    page.openDiagram(node('d2', 'diagram'));
    page.openDiagram(node('d2', 'diagram'));
    expect(page.openTabs()).toEqual(['d2']);
    expect(page.activeTab()).toBe('d2');
  });

  it('prevents unload when a tab is dirty and not when settled', async () => {
    const page = await create();
    const event = jasmine.createSpyObj<BeforeUnloadEvent>('BeforeUnloadEvent', ['preventDefault']);
    page.setStatus('d1', 'saved');
    page.onBeforeUnload(event);
    expect(event.preventDefault).not.toHaveBeenCalled();
    page.setStatus('d1', 'dirty');
    page.onBeforeUnload(event);
    expect(event.preventDefault).toHaveBeenCalled();
  });

  it('asks before closing a tab that is still unsaved after flush, and keeps it on cancel', async () => {
    const page = await create({ open: ['d1'], active: 'd1' });
    const editor = fixture.debugElement.children[0].query((d) => d.componentInstance instanceof DrawioEditorComponent)
      .componentInstance as DrawioEditorComponent;
    spyOn(editor, 'flush').and.resolveTo();
    spyOn(editor, 'status').and.returnValue('error');
    confirm.confirm.and.resolveTo(false);
    await page.closeTab('d1');
    expect(confirm.confirm).toHaveBeenCalledWith('Close without saving?', jasmine.any(String), jasmine.anything());
    expect(page.openTabs()).toEqual(['d1']);
    confirm.confirm.and.resolveTo(true);
    await page.closeTab('d1');
    expect(page.openTabs()).toEqual([]);
  });

  function openEditor(): DrawioEditorComponent {
    return fixture.debugElement.query((d) => d.componentInstance instanceof DrawioEditorComponent)
      .componentInstance as DrawioEditorComponent;
  }

  it('allows leaving without prompting when every open editor settles after flush', async () => {
    const page = await create({ open: ['d1'], active: 'd1' });
    const flush = spyOn(openEditor(), 'flush').and.resolveTo();
    expect(await page.canLeave()).toBeTrue();
    expect(flush).toHaveBeenCalled();
    expect(confirm.confirm).not.toHaveBeenCalled();
  });

  it('asks before leaving when an editor is still unsaved, and stays on decline', async () => {
    const page = await create({ open: ['d1'], active: 'd1' });
    spyOn(openEditor(), 'flush').and.resolveTo();
    spyOn(openEditor(), 'status').and.returnValue('error');
    confirm.confirm.and.resolveTo(false);
    expect(await page.canLeave()).toBeFalse();
    expect(confirm.confirm).toHaveBeenCalledWith(
      'You have unsaved diagram changes. Leave anyway?',
      jasmine.any(String),
      jasmine.anything(),
    );
    confirm.confirm.and.resolveTo(true);
    expect(await page.canLeave()).toBeTrue();
  });

  it('closes a settled tab without prompting', async () => {
    const page = await create({ open: ['d1'], active: 'd1' });
    await page.closeTab('d1');
    expect(confirm.confirm).not.toHaveBeenCalled();
    expect(page.openTabs()).toEqual([]);
  });

  describe('explorer sidebar toggle', () => {
    const pane = () => fixture.nativeElement.querySelector('[data-testid="planner-explorer-pane"]') as HTMLElement;

    beforeEach(() => spyOn(window, 'matchMedia').and.returnValue({ matches: true } as MediaQueryList));
    afterEach(() => localStorage.removeItem(EXPLORER_KEY));

    it('hides the explorer on desktop and remembers the choice', async () => {
      const page = await create();
      expect(page.explorerVisible()).toBeTrue();

      page.toggleExplorer();
      fixture.detectChanges();

      expect(page.explorerVisible()).toBeFalse();
      expect(pane().classList).toContain('md:hidden');
      expect(localStorage.getItem(EXPLORER_KEY)).toBe('hidden');
    });

    it('restores a hidden explorer after reload', async () => {
      localStorage.setItem(EXPLORER_KEY, 'hidden');
      const page = await create();
      expect(page.explorerVisible()).toBeFalse();
    });

    it('toggles with Ctrl+B / Cmd+B like VS Code', async () => {
      const page = await create();
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'b', ctrlKey: true }));
      expect(page.explorerVisible()).toBeFalse();
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'b', metaKey: true }));
      expect(page.explorerVisible()).toBeTrue();
    });
  });

  describe('full screen', () => {
    it('enters full screen via the Fullscreen API and exits when the browser leaves it', async () => {
      const page = await create();
      const root = fixture.nativeElement.querySelector('[data-testid="planner-root"]') as HTMLElement;
      // Whole page goes full screen so app dialogs (unsaved-changes confirm) stay visible above the editor.
      const request = spyOn(document.documentElement, 'requestFullscreen').and.resolveTo();

      await page.toggleFullscreen();
      fixture.detectChanges();
      expect(request).toHaveBeenCalled();
      expect(page.fullscreen()).toBeTrue();
      expect(root.classList).toContain('fixed');

      document.dispatchEvent(new Event('fullscreenchange'));
      expect(page.fullscreen()).toBeFalse();
    });

    it('still fills the window when the Fullscreen API is refused', async () => {
      const page = await create();
      spyOn(document.documentElement, 'requestFullscreen').and.rejectWith(new Error('denied'));

      await page.toggleFullscreen();
      expect(page.fullscreen()).toBeTrue();

      await page.toggleFullscreen();
      expect(page.fullscreen()).toBeFalse();
    });
  });
});
