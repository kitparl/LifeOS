import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import {
  DEFAULT_PINNED_IDS,
  NAV_CATEGORIES_ENABLED,
  NAV_DESTINATIONS,
  NavDestination,
  getDestinationById,
  isSidebarDestination,
} from '../../shared/layout/nav-registry';
import {
  PreferencesApi,
  readJsonLocalStorage,
  writeJsonLocalStorage,
} from './preferences-sync';

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
const PIN_GROUP = 'Pin';
/** Flat-mode group for non-pinned modules; its order is `visible`. */
const FLAT_GROUP = 'Modules';

interface NavGroup {
  category: string;
  items: NavDestination[];
}

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
  private readonly prefsApi = new PreferencesApi(inject(HttpClient));

  private readonly prefs = signal<NavPrefsValue>(buildDefaultPrefs());

  readonly pinnedDestinations = computed(() =>
    NAV_CATEGORIES_ENABLED ? this.categoryOrderedDestinations() : this.flatGroups().flatMap((g) => g.items),
  );

  readonly unpinnedDestinations = computed(() => {
    const visible = new Set(this.prefs().visible);
    return NAV_DESTINATIONS.filter((d) => !visible.has(d.id) && isSidebarDestination(d));
  });

  /** Sidebar/Settings groups: Pin first, then categories — or, when categories are off, Pin + one flat group. */
  readonly navGroups = computed(() => (NAV_CATEGORIES_ENABLED ? this.categoryGroups() : this.flatGroups()));

  init(): void {
    // Seed from localStorage while API loads
    const legacy = this.readLegacyLocal();
    this.prefs.set(migrateFromLegacyPinned(legacy));

    this.prefsApi.get<NavPrefsValue>(PREFS_KEY).subscribe({
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

  /** Reorder within a single category (or Pin, or the flat group). */
  reorderWithinCategory(category: string, fromIndex: number, toIndex: number): void {
    if (fromIndex === toIndex) return;
    const p = structuredClone(this.prefs());
    if (category === FLAT_GROUP) {
      const list = this.flatGroups().find((g) => g.category === FLAT_GROUP)?.items.map((d) => d.id) ?? [];
      if (fromIndex < 0 || fromIndex >= list.length || toIndex < 0 || toIndex >= list.length) return;
      const [moved] = list.splice(fromIndex, 1);
      list.splice(toIndex, 0, moved);
      p.visible = [...list, ...p.visible.filter((id) => !list.includes(id))];
    } else if (category === PIN_GROUP) {
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

  resetToDefault(): void {
    this.commit(buildDefaultPrefs());
  }

  private pinGroup(p: NavPrefsValue): NavGroup {
    return { category: PIN_GROUP, items: this.sidebarItems(p.pinnedTop.filter((id) => p.visible.includes(id))) };
  }

  private flatGroups(): NavGroup[] {
    const p = this.prefs();
    const topSet = new Set(p.pinnedTop);
    const rest: NavGroup = { category: FLAT_GROUP, items: this.sidebarItems(p.visible.filter((id) => !topSet.has(id))) };
    return [this.pinGroup(p), rest].filter((g) => g.items.length > 0);
  }

  private categoryGroups(): NavGroup[] {
    const p = this.prefs();
    const topSet = new Set(p.pinnedTop);
    const groups: NavGroup[] = [this.pinGroup(p)];
    for (const cat of p.categoryOrder) {
      groups.push({
        category: cat,
        items: this.sidebarItems((p.order[cat] || []).filter((id) => p.visible.includes(id) && !topSet.has(id))),
      });
    }
    return groups.filter((g) => g.items.length > 0);
  }

  /** pinnedTop first, then categories, then any visible id missing from the order maps. */
  private categoryOrderedDestinations(): NavDestination[] {
    const p = this.prefs();
    const topSet = new Set(p.pinnedTop);
    const ordered: string[] = [];
    for (const id of p.pinnedTop) {
      if (p.visible.includes(id) && !ordered.includes(id)) ordered.push(id);
    }
    for (const cat of p.categoryOrder) {
      for (const id of p.order[cat] || []) {
        if (p.visible.includes(id) && !topSet.has(id) && !ordered.includes(id)) ordered.push(id);
      }
    }
    for (const id of p.visible) {
      if (!ordered.includes(id)) ordered.push(id);
    }
    return this.sidebarItems(ordered);
  }

  private sidebarItems(ids: string[]): NavDestination[] {
    return ids
      .map((id) => this.resolveDestination(id))
      .filter((d): d is NavDestination => d !== undefined && isSidebarDestination(d));
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
    this.prefsApi.put(PREFS_KEY, value).subscribe({ error: () => undefined });
  }

  private cacheLocal(visible: string[]): void {
    writeJsonLocalStorage(STORAGE_KEY, visible);
  }

  private readLegacyLocal(): string[] {
    const parsed = readJsonLocalStorage<unknown>(STORAGE_KEY, null);
    if (!Array.isArray(parsed)) return [...DEFAULT_PINNED_IDS];
    const valid = parsed.filter(
      (id): id is string => typeof id === 'string' && getDestinationById(id) !== undefined,
    );
    return valid.length > 0 ? valid : [...DEFAULT_PINNED_IDS];
  }
}
