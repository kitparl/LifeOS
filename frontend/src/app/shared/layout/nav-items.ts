export interface NavItem {
  label: string;
  route: string;
  shortLabel?: string;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

export const navGroups: NavGroup[] = [
  {
    label: 'Core',
    items: [
      { label: 'Dashboard', route: '/dashboard', shortLabel: 'Home' },
      { label: 'Tasks', route: '/tasks' },
      { label: 'Calendar', route: '/calendar' },
      { label: 'Notifications', route: '/notifications', shortLabel: 'Alerts' },
      { label: 'Search', route: '/search' },
    ],
  },
  {
    label: 'Health',
    items: [
      { label: 'Habits', route: '/habits' },
      { label: 'Running', route: '/running' },
      { label: 'Mood', route: '/mood' },
      { label: 'Journal', route: '/journal' },
    ],
  },
  {
    label: 'Growth',
    items: [
      { label: 'Goals', route: '/goals' },
      { label: 'Learning', route: '/learning' },
      { label: 'Career', route: '/career' },
      { label: 'Finance', route: '/finance' },
      { label: 'Wishlist', route: '/wishlist' },
    ],
  },
  {
    label: 'Knowledge',
    items: [
      { label: 'Communication', route: '/communication' },
      { label: 'Q&A', route: '/qa' },
      { label: 'Memory', route: '/memory' },
      { label: 'Files', route: '/files' },
      { label: 'OCR', route: '/ocr' },
      { label: 'Voice', route: '/voice' },
    ],
  },
  {
    label: 'Insights',
    items: [
      { label: 'Analytics', route: '/analytics' },
      { label: 'Reports', route: '/reports' },
      { label: 'Timeline', route: '/timeline' },
      { label: 'Life Timeline', route: '/life-timeline', shortLabel: 'Life' },
      { label: 'Predictions', route: '/predictions', shortLabel: 'Future' },
    ],
  },
  {
    label: 'System',
    items: [
      { label: 'Coaches', route: '/coaches' },
      { label: 'Integrations', route: '/integrations' },
      { label: 'Automations', route: '/automations' },
      { label: 'Export', route: '/export' },
      { label: 'Profile', route: '/profile' },
    ],
  },
];

export const primaryMobileNav: NavItem[] = [
  { label: 'Dashboard', route: '/dashboard', shortLabel: 'Home' },
  { label: 'Tasks', route: '/tasks' },
  { label: 'Calendar', route: '/calendar' },
  { label: 'Search', route: '/search' },
];
