import { Provider } from '@angular/core';
import { LoadChildrenCallback } from '@angular/router';
import { DEVELOPER_GUEST_PROVIDERS } from '../developer/developer.routes';
import { NEWS_GUEST_PROVIDERS } from '../news/news.routes';

/** A free tool exposed to logged-out visitors under `/explore/<path>`. */
export interface ExploreTool {
  id: string;
  label: string;
  shortLabel?: string;
  description: string;
  /** Lucide icon name (kebab-case). */
  icon: string;
  /** Route segment under `/explore`. */
  path: string;
  /** Equivalent route in the authenticated app; logged-in visitors are redirected here. */
  authRoute: string;
  /** Route-level providers for the guest mount (e.g. guest-scoped storage). */
  providers?: Provider[];
  loadChildren: LoadChildrenCallback;
}

export const EXPLORE_BASE = '/explore';
export const EXPLORE_HOME_TITLE = 'Explore Tools';

/** Single source for the guest nav, the tool list page, header titles, and the logged-in redirect. */
export const EXPLORE_TOOLS: ExploreTool[] = [
  {
    id: 'developer',
    label: 'Developer',
    description: 'Encoders, formatters, generators, and converters. Everything runs in your browser.',
    icon: 'terminal',
    path: 'developer',
    authRoute: '/developer',
    providers: DEVELOPER_GUEST_PROVIDERS,
    loadChildren: () => import('../developer/developer.routes').then((m) => m.DEVELOPER_ROUTES),
  },
  {
    id: 'news',
    label: 'News',
    description: 'Browse live headlines by category or search. Saving and collections require sign-in.',
    icon: 'newspaper',
    path: 'news',
    authRoute: '/news',
    providers: NEWS_GUEST_PROVIDERS,
    loadChildren: () => import('../news/news.routes').then((m) => m.NEWS_ROUTES),
  },
];

export function exploreToolRoute(tool: ExploreTool): string {
  return `${EXPLORE_BASE}/${tool.path}`;
}

function splitUrl(url: string): { path: string; suffix: string } {
  const index = url.search(/[?#]/);
  return index === -1 ? { path: url, suffix: '' } : { path: url.slice(0, index), suffix: url.slice(index) };
}

function findTool(path: string): { tool: ExploreTool; rest: string[] } | null {
  if (path !== EXPLORE_BASE && !path.startsWith(`${EXPLORE_BASE}/`)) return null;
  const [toolPath, ...rest] = path.slice(EXPLORE_BASE.length).split('/').filter(Boolean);
  const tool = EXPLORE_TOOLS.find((t) => t.path === toolPath);
  return tool ? { tool, rest } : null;
}

/**
 * Maps an Explore URL to its authenticated equivalent, keeping the sub-path, query, and fragment:
 * `/explore/developer/base64?x=1` -> `/developer/base64?x=1`. `/explore` itself or an unknown
 * tool maps to `/` (the user's home).
 */
export function toAuthenticatedUrl(url: string): string {
  const { path, suffix } = splitUrl(url);
  const match = findTool(path);
  if (!match) return '/';
  return [match.tool.authRoute, ...match.rest].join('/') + suffix;
}

export function resolveExploreTitle(url: string): string {
  return findTool(splitUrl(url).path)?.tool.label ?? EXPLORE_HOME_TITLE;
}
