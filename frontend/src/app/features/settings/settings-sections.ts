/**
 * Settings section registry — the single source for the Settings hub's desktop nav,
 * mobile section picker, and section headings.
 *
 * How to add a setting:
 *   1. Create `settings-<name>-section.component.ts`. Render only the controls, inside a
 *      `.panel` — the hub already shows the section's heading and description.
 *   2. Add one entry below (`id` is the `/settings#<id>` deep link; pick an existing category
 *      or append a new one to SETTINGS_CATEGORIES).
 *   3. Import the component in `settings-hub.component.ts` and add an `@case ('<id>')` for it.
 *   4. Optional: for a legacy route, add a `SettingsFragmentRedirectComponent` route in
 *      `app.routes.ts` with `data: { fragment: '<id>' }`.
 */

export const SETTINGS_CATEGORIES = ['Account', 'Connections & data', 'Preferences', 'App'] as const;

export type SettingsCategory = (typeof SETTINGS_CATEGORIES)[number];

export interface SettingsSection {
  id: string;
  label: string;
  category: SettingsCategory;
  description?: string;
}

export const SETTINGS_SECTIONS: readonly SettingsSection[] = [
  { id: 'profile', label: 'Profile', category: 'Account', description: 'Your name, timezone, and username.' },
  { id: 'password', label: 'Password', category: 'Account', description: 'Change the password you sign in with.' },
  {
    id: 'integrations',
    label: 'Integrations',
    category: 'Connections & data',
    description: 'Turn delivery channels on or off. Tokens, chat IDs, and webhooks are managed on the Integrations page.',
  },
  {
    id: 'export',
    label: 'Export',
    category: 'Connections & data',
    description: 'Download your LifeOS data as JSON or CSV (CSV opens in Excel).',
  },
  {
    id: 'sidebar',
    label: 'Sidebar',
    category: 'Preferences',
    description: 'Choose which modules appear in the sidebar and in what order.',
  },
  {
    id: 'home',
    label: 'Default Home',
    category: 'Preferences',
    description: 'The module that opens when you visit the home URL.',
  },
  {
    id: 'editor',
    label: 'Editor',
    category: 'Preferences',
    description: 'Keyboard behaviour for Knowledge Notes, Journal, Writing, and other editors.',
  },
  {
    id: 'news',
    label: 'News',
    category: 'Preferences',
    description: 'Where News opens and how articles are laid out.',
  },
  { id: 'currency', label: 'Currency', category: 'Preferences', description: 'How amounts are displayed across Finance.' },
  {
    id: 'app',
    label: 'App updates',
    category: 'App',
    description: 'Check for a new version or force-reload the installed app.',
  },
];

/** Legacy fragments that now live under a different section. */
const FRAGMENT_ALIASES: Record<string, string> = { notifications: 'integrations' };

export interface SettingsSectionGroup {
  category: SettingsCategory;
  sections: SettingsSection[];
}

export function groupSettingsSections(sections: readonly SettingsSection[] = SETTINGS_SECTIONS): SettingsSectionGroup[] {
  return SETTINGS_CATEGORIES.map((category) => ({
    category,
    sections: sections.filter((s) => s.category === category),
  })).filter((group) => group.sections.length > 0);
}

/** Maps a URL fragment to a registered section, falling back to the first one. */
export function resolveSettingsSection(
  fragment: string | null | undefined,
  sections: readonly SettingsSection[] = SETTINGS_SECTIONS,
): SettingsSection {
  const id = fragment ? (FRAGMENT_ALIASES[fragment] ?? fragment) : null;
  return sections.find((s) => s.id === id) ?? sections[0];
}
