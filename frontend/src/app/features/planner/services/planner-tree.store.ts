import { HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { PlannerNode, PlannerNodeKind } from '../models/planner.models';
import { PlannerApiService } from './planner-api.service';
import { buildTree, compareNodes, filterTree } from './planner-tree';

const NAME_CONFLICT_MESSAGE = 'A file or folder with that name already exists here.';
const FALLBACK_MESSAGE = 'Something went wrong. Please try again.';

@Injectable()
export class PlannerTreeStore {
  private readonly api = inject(PlannerApiService);

  readonly nodes = signal<PlannerNode[]>([]);
  readonly filter = signal('');
  readonly error = signal<string | null>(null);
  readonly expanded = signal<Set<string>>(new Set());

  readonly tree = computed(() => buildTree(this.nodes()));
  readonly visibleTree = computed(() => filterTree(this.tree(), this.filter()));

  async load(): Promise<void> {
    try {
      this.nodes.set(await firstValueFrom(this.api.list()));
    } catch (err) {
      this.fail(err);
    }
  }

  async create(
    parentId: string | null,
    kind: PlannerNodeKind,
    name: string,
  ): Promise<PlannerNode | void> {
    return this.mutate(async () => {
      const created = await firstValueFrom(
        this.api.create({ parent_id: parentId, kind, name }),
      );
      await this.load();
      return created;
    });
  }

  async rename(id: string, name: string): Promise<PlannerNode | void> {
    return this.updateOptimistically(
      id,
      this.nodes().map((n) => (n.id === id ? { ...n, name } : n)),
      { name },
    );
  }

  async move(id: string, parentId: string | null, orderIndex: number): Promise<PlannerNode | void> {
    return this.updateOptimistically(id, this.reordered(id, parentId, orderIndex), {
      parent_id: parentId,
      order_index: orderIndex,
    });
  }

  async duplicate(id: string): Promise<PlannerNode | void> {
    return this.mutate(async () => {
      const copy = await firstValueFrom(this.api.duplicate(id));
      await this.load();
      return copy;
    });
  }

  /** Deletes a node and returns its id plus all descendant ids (for closing tabs). */
  async remove(id: string): Promise<string[]> {
    const removedIds = this.collectSubtreeIds(id);
    const done = await this.mutate(async () => {
      await firstValueFrom(this.api.remove(id));
      await this.load();
      return true;
    });
    return done ? removedIds : [];
  }

  private async updateOptimistically(
    id: string,
    next: PlannerNode[],
    body: { name?: string; parent_id?: string | null; order_index?: number },
  ): Promise<PlannerNode | void> {
    const previous = this.nodes();
    this.nodes.set(next);
    const updated = await this.mutate(async () => {
      const result = await firstValueFrom(this.api.update(id, body));
      await this.load();
      return result;
    });
    if (!updated) this.nodes.set(previous);
    return updated;
  }

  /** Mirrors the server: detach the node, insert at the clamped index, renumber siblings 0..n-1. */
  private reordered(id: string, parentId: string | null, orderIndex: number): PlannerNode[] {
    const nodes = this.nodes();
    const moved = nodes.find((n) => n.id === id);
    if (!moved) return nodes;
    const siblingsOf = (parent: string | null): PlannerNode[] =>
      nodes.filter((n) => n.parent_id === parent && n.id !== id).sort(compareNodes);
    const target = siblingsOf(parentId);
    target.splice(Math.max(0, Math.min(orderIndex, target.length)), 0, { ...moved, parent_id: parentId });
    const renumbered = new Map<string, PlannerNode>();
    const assign = (list: PlannerNode[]): void =>
      list.forEach((n, i) => renumbered.set(n.id, { ...n, order_index: i }));
    assign(target);
    if (moved.parent_id !== parentId) assign(siblingsOf(moved.parent_id));
    return nodes.map((n) => renumbered.get(n.id) ?? n);
  }

  private collectSubtreeIds(id: string): string[] {
    const nodes = this.nodes();
    const ids = [id];
    for (let i = 0; i < ids.length; i++) {
      for (const n of nodes) if (n.parent_id === ids[i]) ids.push(n.id);
    }
    return ids;
  }

  private async mutate<T>(action: () => Promise<T>): Promise<T | void> {
    this.error.set(null);
    try {
      return await action();
    } catch (err) {
      this.fail(err);
    }
  }

  private fail(err: unknown): void {
    if (err instanceof HttpErrorResponse && err.status === 409) {
      this.error.set(NAME_CONFLICT_MESSAGE);
      return;
    }
    const detail = err instanceof HttpErrorResponse ? err.error?.detail : null;
    this.error.set(typeof detail === 'string' ? detail : FALLBACK_MESSAGE);
  }
}
