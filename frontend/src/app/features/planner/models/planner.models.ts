export type PlannerNodeKind = 'project' | 'folder' | 'diagram';

export interface PlannerNode {
  id: string;
  parent_id: string | null;
  kind: PlannerNodeKind;
  name: string;
  order_index: number;
  revision: number;
  created_at: string;
  updated_at: string;
}

export interface PlannerTreeNode {
  node: PlannerNode;
  children: PlannerTreeNode[];
}

export interface PlannerContent {
  content: string;
  revision: number;
}

export type SaveStatus = 'idle' | 'dirty' | 'saving' | 'saved' | 'error' | 'conflict';
