import { CdkDrag, CdkDragDrop, CdkDropList, CdkDropListGroup } from '@angular/cdk/drag-drop';
import { CdkContextMenuTrigger, CdkMenu, CdkMenuItem } from '@angular/cdk/menu';
import { NgTemplateOutlet } from '@angular/common';
import {
  Component,
  ElementRef,
  Injector,
  afterNextRender,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { PlannerNode, PlannerNodeKind, PlannerTreeNode } from '../models/planner.models';
import { canDrop, freeSiblingName } from '../services/planner-tree';
import { PlannerTreeStore } from '../services/planner-tree.store';

const DEFAULT_NAMES: Record<PlannerNodeKind, string> = {
  project: 'New project',
  folder: 'New folder',
  diagram: 'Untitled diagram',
};
const INDENT_PX = 12;

@Component({
  selector: 'app-planner-explorer',
  standalone: true,
  imports: [
    CdkDrag,
    CdkDropList,
    CdkDropListGroup,
    CdkContextMenuTrigger,
    CdkMenu,
    CdkMenuItem,
    LucideDynamicIcon,
    NgTemplateOutlet,
  ],
  template: `
    <div class="flex h-full min-h-0 flex-col" cdkDropListGroup>
      <div class="flex items-center gap-2 border-b border-[var(--border)] p-2">
        <div class="relative min-w-0 flex-1">
          <svg
            class="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-faint)]"
            lucideIcon="search"
            aria-hidden="true"
          ></svg>
          <input
            type="search"
            class="input-field !py-1 !pl-7 text-xs"
            placeholder="Filter"
            aria-label="Filter projects and diagrams"
            [value]="store.filter()"
            (input)="store.filter.set($any($event.target).value)"
          />
        </div>
        <button
          type="button"
          class="btn-secondary !px-2 text-xs"
          title="New project"
          aria-label="New project"
          (click)="create(null, 'project')"
        >
          <svg class="h-4 w-4" lucideIcon="plus" aria-hidden="true"></svg>
        </button>
      </div>

      @if (store.error(); as message) {
        <div
          class="flex items-start gap-2 border-b border-[var(--border)] px-2 py-1 text-xs text-[var(--danger,#c7162b)]"
          role="alert"
        >
          <span class="min-w-0 flex-1">{{ message }}</span>
          <button type="button" class="shrink-0" aria-label="Dismiss error" (click)="store.error.set(null)">
            <svg class="h-3.5 w-3.5" lucideIcon="x" aria-hidden="true"></svg>
          </button>
        </div>
      }

      <div class="min-h-0 flex-1 overflow-y-auto py-1" role="tree">
        <!-- CDK moves the dragged DOM itself; re-creating the tree after a drop resyncs it with the data. -->
        @for (version of [renderVersion()]; track version) {
          <ng-container
            [ngTemplateOutlet]="level"
            [ngTemplateOutletContext]="{ $implicit: store.visibleTree(), depth: 0, parentId: null }"
          />
        }
      </div>
    </div>

    <ng-template #level let-items let-depth="depth" let-parentId="parentId">
      <div
        cdkDropList
        [cdkDropListData]="parentId"
        [cdkDropListDisabled]="isFiltering()"
        (cdkDropListDropped)="onDrop($event)"
      >
        @for (item of items; track item.node.id) {
          <div cdkDrag [cdkDragData]="item.node" [cdkDragDisabled]="isFiltering() || editingId() === item.node.id">
            <div
              class="group flex cursor-pointer items-center gap-1 py-0.5 pr-2 text-sm text-[var(--text)] outline-none hover:bg-[var(--surface-3)] focus-visible:bg-[var(--surface-3)]"
              [class.bg-[var(--surface-3)]]="item.node.id === activeId()"
              [style.padding-left.px]="depth * ${INDENT_PX} + 8"
              role="treeitem"
              tabindex="0"
              [attr.data-node-id]="item.node.id"
              [attr.aria-expanded]="isContainer(item.node) ? isExpanded(item.node.id) : null"
              [attr.aria-selected]="item.node.id === activeId()"
              [cdkContextMenuTriggerFor]="menu"
              [cdkContextMenuTriggerData]="{ node: item.node }"
              (click)="activate(item.node)"
              (dblclick)="isContainer(item.node) && startRename(item.node)"
              (keydown)="onRowKey($event, item)"
            >
              @if (isContainer(item.node)) {
                <svg
                  class="h-3.5 w-3.5 shrink-0 text-[var(--text-faint)]"
                  [lucideIcon]="isExpanded(item.node.id) ? 'chevron-down' : 'chevron-right'"
                  aria-hidden="true"
                ></svg>
              }
              <svg
                class="h-4 w-4 shrink-0 text-[var(--text-muted)]"
                [lucideIcon]="iconFor(item.node)"
                aria-hidden="true"
              ></svg>
              @if (editingId() === item.node.id) {
                <input
                  class="rename-input input-field min-w-0 flex-1 !py-0 text-sm"
                  aria-label="Name"
                  [value]="item.node.name"
                  (click)="$event.stopPropagation()"
                  (dblclick)="$event.stopPropagation()"
                  (keydown)="onRenameKey($event, item.node)"
                  (blur)="commitRename(item.node, $any($event.target).value)"
                />
              } @else {
                <span class="min-w-0 flex-1 truncate">{{ item.node.name }}</span>
              }
            </div>
            @if (isContainer(item.node) && isExpanded(item.node.id)) {
              <ng-container
                [ngTemplateOutlet]="level"
                [ngTemplateOutletContext]="{ $implicit: item.children, depth: depth + 1, parentId: item.node.id }"
              />
            }
          </div>
        }
      </div>
    </ng-template>

    <ng-template #menu let-node="node">
      <div
        class="min-w-40 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] py-1 text-sm shadow-[var(--shadow-md)]"
        cdkMenu
      >
        @if (isContainer(node)) {
          <button type="button" cdkMenuItem class="menu-row" (cdkMenuItemTriggered)="create(node, 'folder')">New folder</button>
          <button type="button" cdkMenuItem class="menu-row" (cdkMenuItemTriggered)="create(node, 'diagram')">New diagram</button>
        }
        <button type="button" cdkMenuItem class="menu-row" (cdkMenuItemTriggered)="startRename(node)">Rename</button>
        <button type="button" cdkMenuItem class="menu-row" (cdkMenuItemTriggered)="store.duplicate(node.id)">Duplicate</button>
        <button type="button" cdkMenuItem class="menu-row" (cdkMenuItemTriggered)="remove(node)">Delete</button>
      </div>
    </ng-template>
  `,
  styles: `
    .menu-row {
      display: block;
      width: 100%;
      padding: 0.25rem 0.75rem;
      text-align: left;
      color: var(--text);
    }
    .menu-row:hover,
    .menu-row:focus-visible {
      background: var(--surface-3);
      outline: none;
    }
  `,
})
export class PlannerExplorerComponent {
  protected readonly store = inject(PlannerTreeStore);
  private readonly confirmService = inject(ConfirmService);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly injector = inject(Injector);

  readonly activeId = input<string | null>(null);
  readonly open = output<PlannerNode>();
  readonly removed = output<string[]>();

  protected readonly editingId = signal<string | null>(null);
  protected readonly renderVersion = signal(0);

  protected isContainer(node: PlannerNode): boolean {
    return node.kind !== 'diagram';
  }

  protected isFiltering(): boolean {
    return this.store.filter().trim().length > 0;
  }

  protected isExpanded(id: string): boolean {
    return this.isFiltering() || this.store.expanded().has(id);
  }

  protected iconFor(node: PlannerNode): string {
    if (node.kind === 'project') return 'folder-kanban';
    if (node.kind === 'diagram') return 'workflow';
    return this.isExpanded(node.id) ? 'folder-open' : 'folder';
  }

  protected activate(node: PlannerNode): void {
    if (node.kind === 'diagram') this.open.emit(node);
    else this.toggle(node.id);
  }

  protected async create(parent: PlannerNode | null, kind: PlannerNodeKind): Promise<void> {
    if (parent) this.setExpanded(parent.id, true);
    const parentId = parent?.id ?? null;
    const name = freeSiblingName(this.store.nodes(), parentId, DEFAULT_NAMES[kind]);
    const created = await this.store.create(parentId, kind, name);
    if (created) this.startRename(created);
  }

  protected startRename(node: PlannerNode): void {
    this.editingId.set(node.id);
    afterNextRender(
      () => {
        const input = this.host.nativeElement.querySelector<HTMLInputElement>('input.rename-input');
        input?.focus();
        input?.select();
      },
      { injector: this.injector },
    );
  }

  protected async commitRename(node: PlannerNode, value: string): Promise<void> {
    if (this.editingId() !== node.id) return;
    this.editingId.set(null);
    const name = value.trim();
    if (name && name !== node.name) await this.store.rename(node.id, name);
  }

  protected onRenameKey(event: KeyboardEvent, node: PlannerNode): void {
    event.stopPropagation();
    if (event.key === 'Enter') {
      void this.commitRename(node, (event.target as HTMLInputElement).value);
    } else if (event.key === 'Escape') {
      this.editingId.set(null);
    }
  }

  protected async remove(node: PlannerNode): Promise<void> {
    const suffix = this.isContainer(node) ? ' and everything in it' : '';
    const confirmed = await this.confirmService.confirm(
      `Delete "${node.name}"${suffix}?`,
      `Delete ${node.kind}`,
    );
    if (!confirmed) return;
    const ids = await this.store.remove(node.id);
    if (ids.length) this.removed.emit(ids);
  }

  protected onRowKey(event: KeyboardEvent, item: PlannerTreeNode): void {
    const node = item.node;
    switch (event.key) {
      case 'ArrowDown':
        this.moveFocus(event, 1);
        break;
      case 'ArrowUp':
        this.moveFocus(event, -1);
        break;
      case 'ArrowRight':
        if (this.isContainer(node)) this.setExpanded(node.id, true);
        break;
      case 'ArrowLeft':
        if (this.isContainer(node)) this.setExpanded(node.id, false);
        break;
      case 'Enter':
        this.activate(node);
        break;
      case 'F2':
        this.startRename(node);
        break;
      case 'Delete':
        void this.remove(node);
        break;
      default:
        return;
    }
    event.preventDefault();
  }

  protected async onDrop(event: CdkDragDrop<string | null>): Promise<void> {
    const dragged = event.item.data as PlannerNode;
    const nodes = this.store.nodes();
    const rowTarget = this.nodeAtDropPoint(event.dropPoint, dragged);
    const target = rowTarget ?? nodes.find((n) => n.id === event.container.data) ?? null;
    if (canDrop(nodes, dragged, target)) {
      const parentId = target?.id ?? null;
      const index = rowTarget
        ? nodes.filter((n) => n.parent_id === parentId).length
        : event.currentIndex;
      const unchanged = !rowTarget && parentId === dragged.parent_id && index === event.previousIndex;
      if (!unchanged) await this.store.move(dragged.id, parentId, index);
    }
    this.renderVersion.update((v) => v + 1);
  }

  /** A folder/project row only counts as a drop target when the pointer is in its middle band. */
  private nodeAtDropPoint(point: { x: number; y: number }, dragged: PlannerNode): PlannerNode | null {
    const row = document
      .elementsFromPoint(point.x, point.y)
      .find((el): el is HTMLElement => el instanceof HTMLElement && el.dataset['nodeId'] !== undefined);
    const id = row?.dataset['nodeId'];
    if (!row || !id || id === dragged.id) return null;
    const rect = row.getBoundingClientRect();
    const inMiddleBand = point.y > rect.top + rect.height * 0.25 && point.y < rect.bottom - rect.height * 0.25;
    const node = this.store.nodes().find((n) => n.id === id);
    return inMiddleBand && node && this.isContainer(node) ? node : null;
  }

  private toggle(id: string): void {
    this.setExpanded(id, !this.store.expanded().has(id));
  }

  private setExpanded(id: string, expanded: boolean): void {
    this.store.expanded.update((set) => {
      const next = new Set(set);
      if (expanded) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  private moveFocus(event: KeyboardEvent, step: number): void {
    const rows = Array.from(this.host.nativeElement.querySelectorAll<HTMLElement>('[data-node-id]'));
    const index = rows.indexOf(event.currentTarget as HTMLElement);
    rows[index + step]?.focus();
  }
}
