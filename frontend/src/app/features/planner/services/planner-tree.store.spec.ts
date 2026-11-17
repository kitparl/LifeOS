import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Subject, of, throwError } from 'rxjs';
import { PlannerNode } from '../models/planner.models';
import { PlannerApiService } from './planner-api.service';
import { buildTree } from './planner-tree';
import { PlannerTreeStore } from './planner-tree.store';

function node(id: string, parent_id: string | null, kind: PlannerNode['kind'], name = id): PlannerNode {
  return { id, parent_id, kind, name, order_index: 0, revision: 1, created_at: '', updated_at: '' };
}

describe('PlannerTreeStore', () => {
  const nodes = [
    node('p', null, 'project', 'Project'),
    node('f', 'p', 'folder'),
    node('d', 'f', 'diagram'),
    node('x', 'p', 'diagram'),
  ];
  let api: jasmine.SpyObj<PlannerApiService>;
  let store: PlannerTreeStore;

  beforeEach(async () => {
    api = jasmine.createSpyObj('PlannerApiService', ['list', 'create', 'update', 'duplicate', 'remove']);
    api.list.and.returnValue(of(nodes));
    TestBed.configureTestingModule({
      providers: [PlannerTreeStore, { provide: PlannerApiService, useValue: api }],
    });
    store = TestBed.inject(PlannerTreeStore);
    await store.load();
  });

  it('rename rolls back and reports the conflict message on 409', async () => {
    api.update.and.returnValue(
      throwError(() => new HttpErrorResponse({ status: 409, error: { detail: 'dup' } })),
    );
    await store.rename('p', 'Taken');
    expect(store.nodes().find((n) => n.id === 'p')?.name).toBe('Project');
    expect(store.error()).toBe('A file or folder with that name already exists here.');
  });

  it('move rolls back and surfaces the server detail on 400', async () => {
    api.update.and.returnValue(
      throwError(() => new HttpErrorResponse({ status: 400, error: { detail: 'Cannot move into itself' } })),
    );
    await store.move('f', 'd', 0);
    expect(store.nodes().find((n) => n.id === 'f')?.parent_id).toBe('p');
    expect(store.error()).toBe('Cannot move into itself');
  });

  it('move renumbers siblings optimistically while the update is pending', () => {
    const abc = [node('a', null, 'project'), node('b', null, 'project'), node('c', null, 'project')].map(
      (n, i) => ({ ...n, order_index: i }),
    );
    store.nodes.set(abc);
    api.update.and.returnValue(new Subject<PlannerNode>());
    void store.move('a', null, 1);
    const order = buildTree(store.nodes()).map((t) => t.node.id);
    expect(order).toEqual(['b', 'a', 'c']);
  });

  it('rename applies optimistically and reloads on success', async () => {
    api.update.and.returnValue(of({ ...nodes[0], name: 'New' }));
    api.list.and.returnValue(of([{ ...nodes[0], name: 'New' }, ...nodes.slice(1)]));
    await store.rename('p', 'New');
    expect(store.nodes().find((n) => n.id === 'p')?.name).toBe('New');
    expect(store.error()).toBeNull();
  });

  it('remove returns the node and all descendant ids', async () => {
    api.remove.and.returnValue(of(undefined));
    api.list.and.returnValue(of([nodes[0], nodes[3]]));
    const ids = await store.remove('f');
    expect(ids.sort()).toEqual(['d', 'f']);
    expect(store.nodes().length).toBe(2);
  });

  it('remove returns no ids when the server rejects', async () => {
    api.remove.and.returnValue(throwError(() => new HttpErrorResponse({ status: 500 })));
    expect(await store.remove('f')).toEqual([]);
    expect(store.error()).toBeTruthy();
  });
});
