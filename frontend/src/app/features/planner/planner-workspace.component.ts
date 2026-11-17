import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  HostListener,
  OnInit,
  computed,
  inject,
  signal,
  viewChild,
  viewChildren,
} from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { ConfirmService } from '../../shared/confirm/confirm.service';
import { SplitBounds, SplitDividerComponent } from '../../shared/split-divider/split-divider.component';
import { DrawioEditorComponent } from './components/drawio-editor.component';
import { PlannerExplorerComponent } from './components/planner-explorer.component';
import { PlannerNode, SaveStatus } from './models/planner.models';
import { PlannerTreeStore } from './services/planner-tree.store';

const STORAGE_KEY = 'lifeos.planner.tabs';
const SETTLED: SaveStatus[] = ['idle', 'saved'];

interface StoredTabs {
  open: string[];
  active: string | null;
}

@Component({
  selector: 'app-planner-workspace',
  standalone: true,
  imports: [PlannerExplorerComponent, DrawioEditorComponent, SplitDividerComponent, LucideDynamicIcon],
  providers: [PlannerTreeStore],
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { class: 'block' },
  template: `
    <div
      #split
      class="relative flex h-[calc(100vh-10rem)] min-h-[24rem] overflow-hidden rounded border border-[var(--border)] bg-[var(--surface-1)]"
      [style.--planner-explorer-w]="splitRatio() * 100 + '%'"
    >
      <aside
        class="z-20 w-72 shrink-0 flex-col border-r border-[var(--border)] bg-[var(--surface-1)] max-md:absolute max-md:inset-y-0 max-md:left-0 md:flex md:w-[var(--planner-explorer-w)]"
        [class.hidden]="!explorerOpen()"
        [class.flex]="explorerOpen()"
        data-testid="planner-explorer-pane"
      >
        <app-planner-explorer
          class="min-h-0 flex-1"
          [activeId]="activeTab()"
          (open)="openDiagram($event)"
          (removed)="closeRemoved($event)"
        />
      </aside>
      <app-split-divider
        class="hidden w-1 shrink-0 cursor-col-resize bg-[var(--border)] hover:bg-[var(--primary)] focus-visible:bg-[var(--primary)] data-[resizing=true]:bg-[var(--primary)] md:block"
        [value]="splitRatio()"
        [min]="splitMin"
        [max]="splitMax"
        [defaultValue]="splitDefault"
        [bounds]="splitBounds"
        label="Resize explorer and editor"
        (valueChange)="splitRatio.set($event)"
      />
      <section class="flex min-w-0 flex-1 flex-col">
        <div class="tab-bar px-2" role="tablist">
          <button
            type="button"
            class="btn-ghost !min-h-8 !px-2 md:hidden"
            aria-label="Toggle explorer"
            data-testid="planner-explorer-toggle"
            (click)="explorerOpen.set(!explorerOpen())"
          >
            <svg class="h-4 w-4" lucideIcon="folder-open" aria-hidden="true"></svg>
          </button>
          @for (id of openTabs(); track id) {
            <div class="flex items-center" (auxclick)="onTabAuxClick($event, id)">
              <button
                type="button"
                role="tab"
                class="tab-bar__btn"
                [class.active]="id === activeTab()"
                [attr.aria-selected]="id === activeTab()"
                [attr.data-tab-id]="id"
                (click)="activeTab.set(id); persist()"
              >
                {{ labels()[id] }}
                @if (isUnsettled(statuses()[id])) {
                  <span
                    class="ml-1 inline-block h-1.5 w-1.5 rounded-full bg-[var(--primary)]"
                    aria-label="Unsaved changes"
                    data-testid="planner-tab-dot"
                  ></span>
                }
              </button>
              <button
                type="button"
                class="btn-ghost !min-h-6 !px-1"
                [attr.aria-label]="'Close ' + labels()[id]"
                (click)="closeTab(id)"
              >
                <svg class="h-3 w-3" lucideIcon="x" aria-hidden="true"></svg>
              </button>
            </div>
          }
        </div>
        <div class="relative min-h-0 flex-1">
          @for (id of openTabs(); track id) {
            <div class="h-full" [class.hidden]="id !== activeTab()">
              <app-drawio-editor [nodeId]="id" (statusChange)="setStatus(id, $event)" />
            </div>
          } @empty {
            <p class="p-6 text-sm text-[var(--text-faint)]">
              Open a diagram from the explorer or create a project to start.
            </p>
          }
        </div>
      </section>
    </div>
  `,
})
export class PlannerWorkspaceComponent implements OnInit {
  private readonly store = inject(PlannerTreeStore);
  private readonly confirmService = inject(ConfirmService);
  private readonly splitEl = viewChild.required<ElementRef<HTMLElement>>('split');
  private readonly editors = viewChildren(DrawioEditorComponent);

  readonly openTabs = signal<string[]>([]);
  readonly activeTab = signal<string | null>(null);
  readonly statuses = signal<Record<string, SaveStatus>>({});
  readonly explorerOpen = signal(false);

  readonly splitMin = 0.15;
  readonly splitMax = 0.5;
  readonly splitDefault = 0.25;
  readonly splitRatio = signal(this.splitDefault);

  readonly labels = computed(() =>
    Object.fromEntries(this.store.nodes().map((n) => [n.id, n.name])) as Record<string, string>,
  );

  readonly splitBounds = (): SplitBounds | null => {
    const rect = this.splitEl().nativeElement.getBoundingClientRect();
    return { start: rect.left, end: rect.right };
  };

  async ngOnInit(): Promise<void> {
    const stored = this.readStored();
    await this.store.load();
    const diagrams = new Set(this.store.nodes().filter((n) => n.kind === 'diagram').map((n) => n.id));
    const open = stored.open.filter((id) => diagrams.has(id));
    this.openTabs.set(open);
    this.activeTab.set(stored.active && open.includes(stored.active) ? stored.active : (open[0] ?? null));
  }

  @HostListener('window:beforeunload', ['$event'])
  onBeforeUnload(event: BeforeUnloadEvent): void {
    if (Object.values(this.statuses()).some((s) => this.isUnsettled(s))) {
      event.preventDefault();
    }
  }

  isUnsettled(status: SaveStatus | undefined): boolean {
    return !!status && !SETTLED.includes(status);
  }

  openDiagram(node: PlannerNode): void {
    if (!this.openTabs().includes(node.id)) {
      this.openTabs.update((tabs) => [...tabs, node.id]);
    }
    this.activeTab.set(node.id);
    this.explorerOpen.set(false);
    this.persist();
  }

  setStatus(id: string, status: SaveStatus): void {
    this.statuses.update((s) => ({ ...s, [id]: status }));
  }

  closeRemoved(ids: string[]): void {
    ids.forEach((id) => this.removeTab(id));
  }

  onTabAuxClick(event: MouseEvent, id: string): void {
    if (event.button === 1) {
      event.preventDefault();
      void this.closeTab(id);
    }
  }

  async closeTab(id: string): Promise<void> {
    const editor = this.editors().find((e) => e.nodeId() === id);
    if (editor) {
      await editor.flush();
      if (!SETTLED.includes(editor.status()) && !(await this.confirmDiscard())) return;
    }
    this.removeTab(id);
  }

  /** Route guard hook: flush every open editor, then confirm if any still holds unsaved changes. */
  async canLeave(): Promise<boolean> {
    const editors = this.editors();
    await Promise.all(editors.map((e) => e.flush()));
    if (editors.every((e) => SETTLED.includes(e.status()))) return true;
    return this.confirmService.confirm('You have unsaved diagram changes. Leave anyway?', 'Unsaved changes', {
      acceptLabel: 'Leave',
    });
  }

  persist(): void {
    const value: StoredTabs = { open: this.openTabs(), active: this.activeTab() };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    } catch {
      /* storage unavailable: tabs just won't be restored */
    }
  }

  private confirmDiscard(): Promise<boolean> {
    return this.confirmService.confirm('Close without saving?', 'Unsaved changes', {
      acceptLabel: 'Close',
    });
  }

  private removeTab(id: string): void {
    const tabs = this.openTabs();
    const index = tabs.indexOf(id);
    if (index < 0) return;
    const next = tabs.filter((t) => t !== id);
    this.openTabs.set(next);
    this.statuses.update(({ [id]: _removed, ...rest }) => rest);
    if (this.activeTab() === id) {
      this.activeTab.set(next[Math.min(index, next.length - 1)] ?? null);
    }
    this.persist();
  }

  private readStored(): StoredTabs {
    try {
      const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? 'null');
      if (Array.isArray(parsed?.open)) {
        return {
          open: parsed.open.filter((id: unknown): id is string => typeof id === 'string'),
          active: typeof parsed.active === 'string' ? parsed.active : null,
        };
      }
    } catch {
      /* corrupt or unavailable storage: start with no tabs */
    }
    return { open: [], active: null };
  }
}
