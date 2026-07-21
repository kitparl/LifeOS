export interface NavDestination {
  id: string;
  label: string;
  route: string;
  shortLabel?: string;
  category?: string;
  hidden?: boolean;
}

export const NAV_DESTINATIONS: NavDestination[] = [
  { id: 'dashboard', label: 'Dashboard', route: '/dashboard', shortLabel: 'Home', category: 'Core' },
  { id: 'tasks', label: 'Tasks', route: '/tasks', category: 'Core' },
  { id: 'calendar', label: 'Calendar', route: '/calendar', category: 'Core' },
  { id: 'running', label: 'Running', route: '/running', category: 'Health' },
  { id: 'habits', label: 'Habits', route: '/habits', category: 'Health' },
  { id: 'goals', label: 'Goals', route: '/goals', category: 'Growth' },
  { id: 'communication', label: 'Communication', route: '/communication', category: 'Knowledge' },
  { id: 'finance', label: 'Finance', route: '/finance', category: 'Growth' },
  { id: 'timeline', label: 'Timeline', route: '/timeline', category: 'Insights' },
  { id: 'insights', label: 'Insights', route: '/insights', category: 'Insights' },
  { id: 'documents', label: 'Documents', route: '/documents', category: 'Knowledge' },
  { id: 'notifications', label: 'Notifications', route: '/notifications', shortLabel: 'Alerts', category: 'Core' },
  { id: 'assistant', label: 'AI Assistant', route: '/assistant', shortLabel: 'AI', category: 'System' },
  { id: 'settings', label: 'Settings', route: '/settings', category: 'System' },
  { id: 'mood', label: 'Mood', route: '/mood', category: 'Health', hidden: true },
  { id: 'journal', label: 'Journal', route: '/journal', category: 'Health' },
  { id: 'learning', label: 'Learning', route: '/learning', category: 'Growth' },
  { id: 'career', label: 'Career', route: '/career', category: 'Growth' },
  { id: 'wishlist', label: 'Wishlist', route: '/wishlist', category: 'Growth' },
  { id: 'qa', label: 'Q&A', route: '/qa', category: 'Knowledge' },
  { id: 'knowledge', label: 'Knowledge Notes', route: '/knowledge', shortLabel: 'Notes', category: 'Knowledge' },
  { id: 'memory', label: 'Memory', route: '/memory', category: 'Knowledge' },
  { id: 'voice', label: 'Voice', route: '/voice', category: 'Knowledge' },
  { id: 'coaches', label: 'Coaches', route: '/coaches', category: 'System' },
  { id: 'integrations', label: 'Integrations', route: '/integrations', category: 'System' },
  { id: 'automations', label: 'Automations', route: '/automations', category: 'System' },
  { id: 'search', label: 'Search', route: '/search', category: 'Core' },
];

export const DEFAULT_PINNED_IDS: string[] = [
  'dashboard',
  'tasks',
  'calendar',
  'running',
  'habits',
  'goals',
  'communication',
  'finance',
  'timeline',
  'insights',
  'documents',
  'notifications',
  'assistant',
  'settings',
];

const destinationById = new Map(NAV_DESTINATIONS.map((d) => [d.id, d]));

export function getDestinationById(id: string): NavDestination | undefined {
  return destinationById.get(id);
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
};

export function resolvePageTitle(url: string): string {
  const legacy = LEGACY_ROUTE_LABELS[url.split('?')[0].split('#')[0]];
  if (legacy) {
    return legacy;
  }
  return getDestinationByRoute(url)?.label ?? 'LifeOS';
}
