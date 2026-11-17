import { PlannerNode, PlannerTreeNode } from '../models/planner.models';

export function compareNodes(a: PlannerNode, b: PlannerNode): number {
  return a.order_index - b.order_index || a.name.localeCompare(b.name);
}

export function buildTree(nodes: PlannerNode[]): PlannerTreeNode[] {
  const byParent = new Map<string | null, PlannerNode[]>();
  for (const node of nodes) {
    const siblings = byParent.get(node.parent_id) ?? [];
    siblings.push(node);
    byParent.set(node.parent_id, siblings);
  }
  const build = (parentId: string | null): PlannerTreeNode[] =>
    (byParent.get(parentId) ?? [])
      .sort(compareNodes)
      .map((node) => ({ node, children: build(node.id) }));
  return build(null);
}

export function filterTree(tree: PlannerTreeNode[], query: string): PlannerTreeNode[] {
  const needle = query.trim().toLowerCase();
  if (!needle) return tree;
  const filter = (items: PlannerTreeNode[]): PlannerTreeNode[] =>
    items.flatMap((item) => {
      const children = filter(item.children);
      return children.length || item.node.name.toLowerCase().includes(needle)
        ? [{ node: item.node, children }]
        : [];
    });
  return filter(tree);
}

/** True when nodeId is ancestorId itself or sits anywhere below it. */
export function isSelfOrDescendant(
  nodes: PlannerNode[],
  ancestorId: string,
  nodeId: string,
): boolean {
  const parentOf = new Map(nodes.map((n) => [n.id, n.parent_id]));
  let current: string | null | undefined = nodeId;
  while (current) {
    if (current === ancestorId) return true;
    current = parentOf.get(current);
  }
  return false;
}

export function canDrop(
  nodes: PlannerNode[],
  dragged: PlannerNode,
  target: PlannerNode | null,
): boolean {
  if (target === null) return dragged.kind === 'project';
  if (target.kind === 'diagram' || dragged.kind === 'project') return false;
  return !isSelfOrDescendant(nodes, dragged.id, target.id);
}

/** First of "base", "base 2", "base 3", … not used (case-insensitively) by a child of parentId. */
export function freeSiblingName(nodes: PlannerNode[], parentId: string | null, base: string): string {
  const taken = new Set(nodes.filter((n) => n.parent_id === parentId).map((n) => n.name.toLowerCase()));
  let candidate = base;
  for (let n = 2; taken.has(candidate.toLowerCase()); n++) candidate = `${base} ${n}`;
  return candidate;
}
