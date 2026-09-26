export interface NavDestination {
  id: string;
  label: string;
  route: string;
  /** Lucide icon name (kebab-case), e.g. "layout-dashboard". */
  icon?: string;
  shortLabel?: string;
  category?: string;
  hidden?: boolean;
  /** `false` keeps a routable module out of the sidebar and Settings sidebar lists (still in ⌘K / Home). */
  sidebar?: boolean;
}

/** Group the sidebar by `category`. Off = flat list; category data is kept so this can be flipped back on. */
export const NAV_CATEGORIES_ENABLED = false;

export const NAV_DESTINATIONS: NavDestination[] = [
  { id: 'analytics', label: 'Analytics', route: '/analytics/dashboard', icon: 'chart-line', shortLabel: 'Home', category: 'Core' },
  { id: 'dashboard', label: 'Quick Action', route: '/quick-action', icon: 'layout-dashboard', shortLabel: 'Quick', category: 'Core' },
  { id: 'tasks', label: 'Tasks', route: '/tasks', icon: 'list-todo', category: 'Core' },
  { id: 'calendar', label: 'Calendar', route: '/calendar', icon: 'calendar-days', category: 'Core' },
  { id: 'routines', label: 'Routines', route: '/routines', icon: 'refresh-cw', category: 'Core' },
  { id: 'running', label: 'Running', route: '/running', icon: 'footprints', category: 'Health' },
  { id: 'habits', label: 'Habits', route: '/habits', icon: 'flame', category: 'Health' },
  { id: 'goals', label: 'Goals', route: '/goals', icon: 'target', category: 'Growth' },
  { id: 'communication', label: 'Communication', route: '/communication', icon: 'message-square', category: 'Knowledge' },
  { id: 'finance', label: 'Finance', route: '/finance', icon: 'wallet', category: 'Growth' },
  { id: 'timeline', label: 'Timeline', route: '/timeline', icon: 'route', category: 'Insights' },
  { id: 'insights', label: 'Insights', route: '/insights', icon: 'chart-column', category: 'Insights' },
  { id: 'documents', label: 'Documents', route: '/documents', icon: 'file-text', category: 'Knowledge' },
  { id: 'notifications', label: 'Notifications', route: '/notifications', icon: 'bell', shortLabel: 'Alerts', category: 'Core', sidebar: false },
  { id: 'assistant', label: 'AI Assistant', route: '/assistant', icon: 'sparkles', shortLabel: 'AI', category: 'System' },
  { id: 'settings', label: 'Settings', route: '/settings', icon: 'settings', category: 'System' },
  { id: 'mood', label: 'Mood', route: '/mood', icon: 'smile', category: 'Health', hidden: true },
  { id: 'journal', label: 'Journal', route: '/journal', icon: 'book-open', category: 'Health' },
  { id: 'learning', label: 'Learning', route: '/learning', icon: 'graduation-cap', category: 'Growth' },
  { id: 'career', label: 'Career', route: '/career', icon: 'briefcase-business', category: 'Growth' },
  { id: 'wishlist', label: 'Wishlist', route: '/wishlist', icon: 'star', category: 'Growth' },
  { id: 'sticky-notes', label: 'Quick Note', route: '/notes', icon: 'sticky-note', shortLabel: 'Note', category: 'Core' },
  { id: 'news', label: 'News', route: '/news', icon: 'newspaper', category: 'Knowledge' },
  { id: 'qa', label: 'Q&A', route: '/qa', icon: 'circle-help', category: 'Knowledge' },
  { id: 'knowledge', label: 'Knowledge Notes', route: '/knowledge', icon: 'notebook-pen', shortLabel: 'Notes', category: 'Knowledge' },
  { id: 'memory', label: 'Memory', route: '/memory', icon: 'brain', category: 'Knowledge' },
  { id: 'voice', label: 'Voice', route: '/voice', icon: 'mic', category: 'Knowledge' },
  { id: 'coaches', label: 'Coaches', route: '/coaches', icon: 'users', category: 'System' },
  { id: 'integrations', label: 'Integrations', route: '/integrations', icon: 'plug', category: 'System' },
  { id: 'automations', label: 'Automations', route: '/automations', icon: 'zap', category: 'System' },
  { id: 'search', label: 'Search', route: '/search', icon: 'search', category: 'Core' },
  { id: 'developer', label: 'Developer', route: '/developer', icon: 'terminal', category: 'System' },
];

/** Module that opens at `/` when the user has no valid home preference. */
export const DEFAULT_HOME_MODULE_ID = 'dashboard';

export const DEFAULT_PINNED_IDS: string[] = [
  'dashboard',
  'tasks',
  'calendar',
  'routines',
  'running',
  'habits',
  'goals',
  'communication',
  'finance',
  'timeline',
  'insights',
  'settings',
  'sticky-notes',
];

const destinationById = new Map(NAV_DESTINATIONS.map((d) => [d.id, d]));

export function getDestinationById(id: string): NavDestination | undefined {
  return destinationById.get(id);
}

export function isSidebarDestination(dest: NavDestination): boolean {
  return !dest.hidden && dest.sidebar !== false;
}

export function isAvailableHomeModule(id: string): boolean {
  const dest = getDestinationById(id);
  return Boolean(dest && !dest.hidden);
}

export function availableHomeDestinations(): NavDestination[] {
  return NAV_DESTINATIONS.filter((d) => !d.hidden);
}

export function groupedHomeDestinations(): { category: string; items: NavDestination[] }[] {
  const groups: { category: string; items: NavDestination[] }[] = [];
  const index = new Map<string, number>();
  for (const dest of availableHomeDestinations()) {
    const category = dest.category ?? 'Other';
    let i = index.get(category);
    if (i === undefined) {
      i = groups.length;
      index.set(category, i);
      groups.push({ category, items: [] });
    }
    groups[i].items.push(dest);
  }
  return groups;
}

export function homeRouteFor(moduleId: string): string {
  const dest = isAvailableHomeModule(moduleId)
    ? getDestinationById(moduleId)
    : getDestinationById(DEFAULT_HOME_MODULE_ID);
  return dest?.route ?? '/quick-action';
}

export function getDestinationByRoute(url: string): NavDestination | undefined {
  const path = url.split('?')[0].split('#')[0];
  const sorted = [...NAV_DESTINATIONS].sort((a, b) => b.route.length - a.route.length);
  return sorted.find((d) => path === d.route || path.startsWith(`${d.route}/`));
}

/** Legacy redirect routes map to hub titles for the shell header. */
const LEGACY_ROUTE_LABELS: Record<string, string> = {
  '/analytics': 'Insights',
  '/reports': 'Insights',
  '/predictions': 'Insights',
  '/life-timeline': 'Timeline',
  '/files': 'Documents',
  '/ocr': 'Documents',
  '/profile': 'Settings',
  '/export': 'Settings',
  '/dashboard': 'Quick Action',
};

export function resolvePageTitle(url: string): string {
  const legacy = LEGACY_ROUTE_LABELS[url.split('?')[0].split('#')[0]];
  if (legacy) {
    return legacy;
  }
  return getDestinationByRoute(url)?.label ?? 'LifeOS';
}
