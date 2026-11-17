import { CdkDrag, CdkDragDrop } from '@angular/cdk/drag-drop';
import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { NAV_LUCIDE_ICON_PROVIDERS } from '../../../shared/layout/nav-lucide';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { PlannerNode } from '../models/planner.models';
import { buildTree, filterTree } from '../services/planner-tree';
import { PlannerTreeStore } from '../services/planner-tree.store';
import { PlannerExplorerComponent } from './planner-explorer.component';

function node(id: string, parent_id: string | null, kind: PlannerNode['kind'], name = id): PlannerNode {
  return { id, parent_id, kind, name, order_index: 0, revision: 1, created_at: '', updated_at: '' };
}

describe('PlannerExplorerComponent', () => {
  const nodes = [
    node('p', null, 'project', 'Proj'),
    { ...node('f', 'p', 'folder', 'Folder'), order_index: 0 },
    { ...node('d', 'p', 'diagram', 'Diag'), order_index: 1 },
    node('h', 'f', 'folder', 'Inner'),
  ];
  let fixture: ComponentFixture<PlannerExplorerComponent>;
  let store: {
    nodes: ReturnType<typeof signal<PlannerNode[]>>;
    filter: ReturnType<typeof signal<string>>;
    error: ReturnType<typeof signal<string | null>>;
    expanded: ReturnType<typeof signal<Set<string>>>;
    visibleTree: () => ReturnType<typeof buildTree>;
    remove: jasmine.Spy;
    create: jasmine.Spy;
    rename: jasmine.Spy;
    move: jasmine.Spy;
    duplicate: jasmine.Spy;
  };
  let confirm: jasmine.SpyObj<ConfirmService>;

  beforeEach(() => {
    const nodeSignal = signal(nodes);
    const filter = signal('');
    store = {
      nodes: nodeSignal,
      filter,
      error: signal<string | null>(null),
      expanded: signal(new Set<string>(['p', 'f'])),
      visibleTree: () => filterTree(buildTree(nodeSignal()), filter()),
      remove: jasmine.createSpy('remove').and.resolveTo(['d']),
      create: jasmine.createSpy('create').and.resolveTo(node('n', 'p', 'folder', 'New folder')),
      rename: jasmine.createSpy('rename').and.resolveTo(undefined),
      move: jasmine.createSpy('move').and.resolveTo(undefined),
      duplicate: jasmine.createSpy('duplicate').and.resolveTo(undefined),
    };
    confirm = jasmine.createSpyObj('ConfirmService', ['confirm']);
    TestBed.configureTestingModule({
      imports: [PlannerExplorerComponent],
      providers: [
        ...NAV_LUCIDE_ICON_PROVIDERS,
        { provide: PlannerTreeStore, useValue: store },
        { provide: ConfirmService, useValue: confirm },
      ],
    });
    fixture = TestBed.createComponent(PlannerExplorerComponent);
    fixture.detectChanges();
  });

  const row = (id: string): HTMLElement =>
    fixture.nativeElement.querySelector(`[data-node-id="${id}"]`);

  it('emits open when a diagram row is clicked', () => {
    const opened: PlannerNode[] = [];
    fixture.componentInstance.open.subscribe((n) => opened.push(n));
    row('d').click();
    expect(opened.map((n) => n.id)).toEqual(['d']);
  });

  it('removes and emits ids when Delete is confirmed', async () => {
    confirm.confirm.and.resolveTo(true);
    const removed: string[][] = [];
    fixture.componentInstance.removed.subscribe((ids) => removed.push(ids));
    row('d').dispatchEvent(new KeyboardEvent('keydown', { key: 'Delete', bubbles: true }));
    await fixture.whenStable();
    expect(store.remove).toHaveBeenCalledWith('d');
    expect(removed).toEqual([['d']]);
  });

  it('does nothing when Delete is declined', async () => {
    confirm.confirm.and.resolveTo(false);
    const removed: string[][] = [];
    fixture.componentInstance.removed.subscribe((ids) => removed.push(ids));
    row('d').dispatchEvent(new KeyboardEvent('keydown', { key: 'Delete', bubbles: true }));
    await fixture.whenStable();
    expect(store.remove).not.toHaveBeenCalled();
    expect(removed).toEqual([]);
  });

  it('sets store.filter when typing in the filter box', () => {
    const input: HTMLInputElement = fixture.nativeElement.querySelector('input[type="search"]');
    input.value = 'abc';
    input.dispatchEvent(new Event('input'));
    expect(store.filter()).toBe('abc');
  });

  it('renames inline on F2 and commits on Enter', async () => {
    row('d').dispatchEvent(new KeyboardEvent('keydown', { key: 'F2', bubbles: true }));
    fixture.detectChanges();
    const input: HTMLInputElement = fixture.nativeElement.querySelector('input.rename-input');
    input.value = 'Renamed';
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    await fixture.whenStable();
    expect(store.rename).toHaveBeenCalledWith('d', 'Renamed');
  });

  it('creates with the first free default name among the parent\'s children', async () => {
    store.nodes.set([...nodes, node('x', 'p', 'folder', 'New folder')]);
    await fixture.componentInstance['create'](nodes[0], 'folder');
    expect(store.create).toHaveBeenCalledWith('p', 'folder', 'New folder 2');
  });

  it('disables dragging only for the row being renamed', () => {
    row('d').dispatchEvent(new KeyboardEvent('keydown', { key: 'F2', bubbles: true }));
    fixture.detectChanges();
    const disabled = fixture.debugElement
      .queryAll(By.directive(CdkDrag))
      .map((d) => [(d.injector.get(CdkDrag).data as PlannerNode).id, d.injector.get(CdkDrag).disabled]);
    expect(disabled).toContain(['d', true]);
    expect(disabled).toContain(['f', false]);
  });

  describe('onDrop', () => {
    const byId = (id: string): PlannerNode => nodes.find((n) => n.id === id) as PlannerNode;

    function drop(
      id: string,
      containerId: string | null,
      currentIndex: number,
      previousIndex: number,
      overRowId?: string,
    ): Promise<void> {
      const over = overRowId ? row(overRowId) : null;
      const rect = over?.getBoundingClientRect();
      spyOn(document, 'elementsFromPoint').and.returnValue(over ? [over] : []);
      const event = {
        item: { data: byId(id) },
        container: { data: containerId },
        currentIndex,
        previousIndex,
        dropPoint: { x: rect?.left ?? 0, y: rect ? rect.top + rect.height / 2 : 0 },
      } as unknown as CdkDragDrop<string | null>;
      return fixture.componentInstance['onDrop'](event);
    }

    it('moves into a folder row at the end of its children', async () => {
      await drop('d', 'p', 1, 1, 'f');
      expect(store.move).toHaveBeenCalledWith('d', 'f', 1);
    });

    it('reorders within the same parent', async () => {
      await drop('d', 'p', 0, 1);
      expect(store.move).toHaveBeenCalledWith('d', 'p', 0);
    });

    it('moves across parents using the list index', async () => {
      await drop('d', 'f', 0, 1);
      expect(store.move).toHaveBeenCalledWith('d', 'f', 0);
    });

    it('does not move when dropped back in place', async () => {
      await drop('d', 'p', 1, 1);
      expect(store.move).not.toHaveBeenCalled();
    });

    it('rejects dropping a folder into its own descendant', async () => {
      await drop('f', 'f', 0, 0, 'h');
      expect(store.move).not.toHaveBeenCalled();
    });

    it('rejects dropping a project onto a folder', async () => {
      await drop('p', null, 0, 0, 'f');
      expect(store.move).not.toHaveBeenCalled();
    });

    it('re-renders the tree after a rejected drop', async () => {
      const before = row('d');
      await drop('p', null, 0, 0, 'f');
      fixture.detectChanges();
      expect(row('d')).not.toBe(before);
    });
  });
});
