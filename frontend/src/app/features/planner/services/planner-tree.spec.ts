import { PlannerNode, PlannerNodeKind } from '../models/planner.models';
import { buildTree, canDrop, filterTree, freeSiblingName } from './planner-tree';

function node(
  id: string,
  kind: PlannerNodeKind,
  parent_id: string | null,
  name = id,
  order_index = 0,
): PlannerNode {
  return { id, kind, parent_id, name, order_index, revision: 1, created_at: '', updated_at: '' };
}

describe('planner-tree', () => {
  const nodes = [
    node('p', 'project', null),
    node('f1', 'folder', 'p'),
    node('f2', 'folder', 'f1'),
    node('d1', 'diagram', 'f2', 'Deep Flow'),
    node('d2', 'diagram', 'p', 'Other'),
  ];

  it('buildTree sorts siblings by order_index then name', () => {
    const tree = buildTree([
      node('p', 'project', null),
      node('b', 'diagram', 'p', 'B', 1),
      node('z', 'diagram', 'p', 'Z', 0),
      node('a', 'diagram', 'p', 'A', 1),
    ]);
    expect(tree[0].children.map((c) => c.node.id)).toEqual(['z', 'a', 'b']);
  });

  it('filterTree keeps the ancestor chain of a deep match and drops other branches', () => {
    const result = filterTree(buildTree(nodes), 'deep');
    expect(result.length).toBe(1);
    expect(result[0].children.map((c) => c.node.id)).toEqual(['f1']);
    expect(result[0].children[0].children[0].children[0].node.id).toBe('d1');
  });

  it('filterTree returns the input for an empty query', () => {
    const tree = buildTree(nodes);
    expect(filterTree(tree, '')).toBe(tree);
  });

  describe('canDrop', () => {
    const byId = (id: string) => nodes.find((n) => n.id === id)!;
    it('rejects a folder into its own descendant or itself', () => {
      expect(canDrop(nodes, byId('f1'), byId('f2'))).toBe(false);
      expect(canDrop(nodes, byId('f1'), byId('f1'))).toBe(false);
    });
    it('rejects diagram to root, anything into a diagram, project into a folder', () => {
      expect(canDrop(nodes, byId('d2'), null)).toBe(false);
      expect(canDrop(nodes, byId('f1'), byId('d2'))).toBe(false);
      expect(canDrop(nodes, byId('p'), byId('f1'))).toBe(false);
    });
    it('allows valid moves', () => {
      expect(canDrop(nodes, byId('p'), null)).toBe(true);
      expect(canDrop(nodes, byId('d1'), byId('p'))).toBe(true);
      expect(canDrop(nodes, byId('f2'), byId('p'))).toBe(true);
    });
  });

  describe('freeSiblingName', () => {
    it('returns the base name when no sibling uses it', () => {
      expect(freeSiblingName(nodes, 'p', 'New folder')).toBe('New folder');
    });

    it('numbers past taken names, case-insensitively, only among siblings of the parent', () => {
      const all = [
        ...nodes,
        node('a', 'diagram', 'p', 'untitled DIAGRAM'),
        node('b', 'diagram', 'p', 'Untitled diagram 2'),
        node('c', 'diagram', 'f1', 'Untitled diagram 3'),
      ];
      expect(freeSiblingName(all, 'p', 'Untitled diagram')).toBe('Untitled diagram 3');
      expect(freeSiblingName(all, 'f1', 'Untitled diagram')).toBe('Untitled diagram');
    });

    it('treats a null parent as the root level', () => {
      expect(freeSiblingName(nodes, null, 'p')).toBe('p 2');
    });
  });
});
