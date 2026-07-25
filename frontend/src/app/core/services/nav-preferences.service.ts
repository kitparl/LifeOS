import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import {
  DEFAULT_PINNED_IDS,
  NAV_DESTINATIONS,
  NavDestination,
  getDestinationById,
} from '../../shared/layout/nav-registry';
import { environment } from '../../../environments/environment';

export interface NavPrefsValue {
  categoryOrder: string[];
  moduleCategory: Record<string, string>;
  order: Record<string, string[]>;
  pinnedTop: string[];
  visible: string[];
}

const STORAGE_KEY = 'lifeos-nav-pinned';
const PREFS_KEY = 'nav';
const DEFAULT_CATEGORY_ORDER = ['Core', 'Health', 'Growth', 'Knowledge', 'Insights', 'System'];

function defaultModuleCategory(): Record<string, string> {
  const map: Record<string, string> = {};
  for (const d of NAV_DESTINATIONS) {
    if (d.category) map[d.id] = d.category;
  }
  return map;
}

function buildDefaultPrefs(visibleIds: string[] = DEFAULT_PINNED_IDS): NavPrefsValue {
  const moduleCategory = defaultModuleCategory();
  const order: Record<string, string[]> = {};
  for (const id of visibleIds) {
    const cat = moduleCategory[id] ?? 'Other';
    if (!order[cat]) order[cat] = [];
    order[cat].push(id);
  }
  return {
    categoryOrder: [...DEFAULT_CATEGORY_ORDER],
    moduleCategory,
    order,
    pinnedTop: [],
    visible: [...visibleIds],
  };
}

function migrateFromLegacyPinned(ids: string[]): NavPrefsValue {
  return buildDefaultPrefs(ids.length ? ids : DEFAULT_PINNED_IDS);
}

@Injectable({ providedIn: 'root' })
export class NavPreferencesService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/preferences`;

  private readonly prefs = signal<NavPrefsValue>(buildDefaultPrefs());

  readonly pinnedDestinations = computed(() => {
    const p = this.prefs();
    const topSet = new Set(p.pinnedTop);
    const ordered: string[] = [];
    // Flat visible order: pinnedTop first, then categories
    for (const id of p.pinnedTop) {
      if (p.visible.includes(id) && !ordered.includes(id)) ordered.push(id);
    }
    for (const cat of p.categoryOrder) {
      for (const id of p.order[cat] || []) {
        if (p.visible.includes(id) && !topSet.has(id) && !ordered.includes(id)) {
          ordered.push(id);
        }
      }
    }
    // Any remaining visible not in order maps
    for (const id of p.visible) {
      if (!ordered.includes(id)) ordered.push(id);
    }
    return ordered
      .map((id) => this.resolveDestination(id))
      .filter((d): d is NavDestination => d !== undefined && !d.hidden);
  });

  readonly unpinnedDestinations = computed(() => {
    const visible = new Set(this.prefs().visible);
    return NAV_DESTINATIONS.filter((d) => !visible.has(d.id) && !d.hidden);
  });

  readonly settingsDestinations = computed(() => [
    ...this.pinnedDestinations(),
    ...this.unpinnedDestinations(),
  ]);

  /** Grouped view for sidebar: Pin first, then categories. */
  readonly navGroups = computed(() => {
    const p = this.prefs();
    const groups: { category: string; items: NavDestination[] }[] = [];
    const topSet = new Set(p.pinnedTop);
    const pinItems = p.pinnedTop
      .filter((id) => p.visible.includes(id))
      .map((id) => this.resolveDestination(id))
      .filter((d): d is NavDestination => !!d && !d.hidden);
    if (pinItems.length) {
      groups.push({ category: 'Pin', items: pinItems });
    }
    for (const cat of p.categoryOrder) {
      const items = (p.order[cat] || [])
        .filter((id) => p.visible.includes(id) && !topSet.has(id))
        .map((id) => this.resolveDestination(id))
        .filter((d): d is NavDestination => !!d && !d.hidden);
      if (items.length) {
        groups.push({ category: cat, items });
      }
    }
    return groups;
  });

  readonly pinnedTopIds = computed(() => this.prefs().pinnedTop);
  readonly prefsSnapshot = computed(() => this.prefs());

  init(): void {
    // Seed from localStorage while API loads
    const legacy = this.readLegacyLocal();
    this.prefs.set(migrateFromLegacyPinned(legacy));

    this.http.get<{ key: string; value: NavPrefsValue | null }>(`${this.api}/${PREFS_KEY}`).subscribe({
      next: (resp) => {
        if (resp.value && typeof resp.value === 'object' && Array.isArray(resp.value.visible)) {
          this.prefs.set(this.normalize(resp.value));
          this.cacheLocal(resp.value.visible);
        } else if (legacy.length) {
          // One-time migration: push localStorage pins to API
          const migrated = migrateFromLegacyPinned(legacy);
          this.prefs.set(migrated);
          this.saveToApi(migrated);
        }
      },
      error: () => {
        // Offline / unauthenticated — keep local seed
      },
    });
  }

  isPinned(id: string): boolean {
    return this.prefs().visible.includes(id);
  }

  isPinnedTop(id: string): boolean {
    return this.prefs().pinnedTop.includes(id);
  }

  pin(id: string): void {
    if (!getDestinationById(id) || this.isPinned(id)) return;
    const p = structuredClone(this.prefs());
    p.visible = [...p.visible, id];
    const cat = p.moduleCategory[id] ?? getDestinationById(id)?.category ?? 'Other';
    p.moduleCategory[id] = cat;
    if (!p.order[cat]) p.order[cat] = [];
    if (!p.order[cat].includes(id)) p.order[cat].push(id);
    if (!p.categoryOrder.includes(cat)) p.categoryOrder.push(cat);
    this.commit(p);
  }

  unpin(id: string): void {
    const p = structuredClone(this.prefs());
    p.visible = p.visible.filter((x) => x !== id);
    p.pinnedTop = p.pinnedTop.filter((x) => x !== id);
    for (const cat of Object.keys(p.order)) {
      p.order[cat] = (p.order[cat] || []).filter((x) => x !== id);
    }
    this.commit(p);
  }

  togglePin(id: string): void {
    if (this.isPinned(id)) this.unpin(id);
    else this.pin(id);
  }

  pinTop(id: string): void {
    if (!this.isPinned(id)) this.pin(id);
    const p = structuredClone(this.prefs());
    if (!p.pinnedTop.includes(id)) {
      p.pinnedTop = [...p.pinnedTop, id];
    }
    this.commit(p);
  }

  unpinTop(id: string): void {
    const p = structuredClone(this.prefs());
    p.pinnedTop = p.pinnedTop.filter((x) => x !== id);
    this.commit(p);
  }

  togglePinTop(id: string): void {
    if (this.isPinnedTop(id)) this.unpinTop(id);
    else this.pinTop(id);
  }

  /** Flat reorder (legacy) — maps to category of the moved item. */
  reorder(fromIndex: number, toIndex: number): void {
    const ids = this.pinnedDestinations().map((d) => d.id);
    if (fromIndex < 0 || fromIndex >= ids.length || toIndex < 0 || toIndex >= ids.length) return;
    const [moved] = ids.splice(fromIndex, 1);
    ids.splice(toIndex, 0, moved);
    this.setPinnedOrder(ids);
  }

  setPinnedOrder(ids: string[]): void {
    const p = structuredClone(this.prefs());
    const valid = ids.filter((id) => p.visible.includes(id));
    // Rebuild order maps preserving categories for non-top items
    const topSet = new Set(p.pinnedTop);
    p.pinnedTop = valid.filter((id) => topSet.has(id));
    const newOrder: Record<string, string[]> = {};
    for (const id of valid) {
      if (topSet.has(id)) continue;
      const cat = p.moduleCategory[id] ?? getDestinationById(id)?.category ?? 'Other';
      if (!newOrder[cat]) newOrder[cat] = [];
      newOrder[cat].push(id);
    }
    p.order = newOrder;
    p.visible = [...new Set([...valid, ...p.visible.filter((id) => !valid.includes(id))])];
    this.commit(p);
  }

  /** Reorder within a single category (or Pin). */
  reorderWithinCategory(category: string, fromIndex: number, toIndex: number): void {
    if (fromIndex === toIndex) return;
    const p = structuredClone(this.prefs());
    if (category === 'Pin') {
      const list = [...p.pinnedTop];
      if (fromIndex < 0 || fromIndex >= list.length || toIndex < 0 || toIndex >= list.length) return;
      const [moved] = list.splice(fromIndex, 1);
      list.splice(toIndex, 0, moved);
      p.pinnedTop = list;
    } else {
      const list = [...(p.order[category] || [])];
      if (fromIndex < 0 || fromIndex >= list.length || toIndex < 0 || toIndex >= list.length) return;
      const [moved] = list.splice(fromIndex, 1);
      list.splice(toIndex, 0, moved);
      p.order[category] = list;
    }
    this.commit(p);
  }

  moveUp(id: string): void {
    const ids = this.pinnedDestinations().map((d) => d.id);
    const index = ids.indexOf(id);
    if (index > 0) this.reorder(index, index - 1);
  }

  moveDown(id: string): void {
    const ids = this.pinnedDestinations().map((d) => d.id);
    const index = ids.indexOf(id);
    if (index >= 0 && index < ids.length - 1) this.reorder(index, index + 1);
  }

  resetToDefault(): void {
    this.commit(buildDefaultPrefs());
  }

  private resolveDestination(id: string): NavDestination | undefined {
    const base = getDestinationById(id);
    if (!base) return undefined;
    const cat = this.prefs().moduleCategory[id] ?? base.category;
    return { ...base, category: cat };
  }

  private normalize(raw: NavPrefsValue): NavPrefsValue {
    const base = buildDefaultPrefs(raw.visible?.length ? raw.visible : DEFAULT_PINNED_IDS);
    return {
      categoryOrder: raw.categoryOrder?.length ? raw.categoryOrder : base.categoryOrder,
      moduleCategory: { ...base.moduleCategory, ...(raw.moduleCategory || {}) },
      order: { ...base.order, ...(raw.order || {}) },
      pinnedTop: Array.isArray(raw.pinnedTop) ? raw.pinnedTop.filter((id) => getDestinationById(id)) : [],
      visible: (raw.visible || base.visible).filter((id) => getDestinationById(id)),
    };
  }

  private commit(p: NavPrefsValue): void {
    const normalized = this.normalize(p);
    this.prefs.set(normalized);
    this.cacheLocal(normalized.visible);
    this.saveToApi(normalized);
  }

  private saveToApi(value: NavPrefsValue): void {
    this.http.put(`${this.api}/${PREFS_KEY}`, { value }).subscribe({ error: () => undefined });
  }

  private cacheLocal(visible: string[]): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(visible));
    } catch {
      /* ignore */
    }
  }

  private readLegacyLocal(): string[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [...DEFAULT_PINNED_IDS];
      const parsed = JSON.parse(raw) as unknown;
      if (!Array.isArray(parsed)) return [...DEFAULT_PINNED_IDS];
      const valid = parsed.filter(
        (id): id is string => typeof id === 'string' && getDestinationById(id) !== undefined,
      );
      return valid.length > 0 ? valid : [...DEFAULT_PINNED_IDS];
    } catch {
      return [...DEFAULT_PINNED_IDS];
    }
  }
}
