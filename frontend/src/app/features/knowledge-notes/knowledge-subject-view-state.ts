/**
 * Per-browser view state for the subject page (localStorage): which chapters are expanded,
 * the last-opened section per chapter, the last-edited section, and the sidebar width.
 */

const SIDEBAR_KEY = 'lifeos.kn.sidebarWidth';
const EXPANDED_PREFIX = 'lifeos.kn.expanded.';
const LAST_SECTION_PREFIX = 'lifeos.kn.lastSection.';
const LAST_EDITED_PREFIX = 'lifeos.kn.lastEdited.';

export const SIDEBAR_DEFAULT = 256;
export const SIDEBAR_MIN = 180;
export const SIDEBAR_MAX = 480;

export function readLastEdited(subjectId: string): string | null {
  return localStorage.getItem(LAST_EDITED_PREFIX + subjectId);
}

export function writeLastEdited(subjectId: string, sectionId: string): void {
  localStorage.setItem(LAST_EDITED_PREFIX + subjectId, sectionId);
}

export function readExpandedChapters(subjectId: string): Set<string> {
  try {
    const raw = localStorage.getItem(EXPANDED_PREFIX + subjectId);
    return new Set(raw ? (JSON.parse(raw) as string[]) : []);
  } catch {
    return new Set();
  }
}

export function writeExpandedChapters(subjectId: string, chapterIds: Set<string>): void {
  localStorage.setItem(EXPANDED_PREFIX + subjectId, JSON.stringify(Array.from(chapterIds)));
}

export function readLastSections(subjectId: string): Record<string, string> {
  try {
    const raw = localStorage.getItem(LAST_SECTION_PREFIX + subjectId);
    return raw ? (JSON.parse(raw) as Record<string, string>) : {};
  } catch {
    return {};
  }
}

export function writeLastSections(subjectId: string, sectionByChapter: Record<string, string>): void {
  localStorage.setItem(LAST_SECTION_PREFIX + subjectId, JSON.stringify(sectionByChapter));
}

export function readSidebarWidth(): number {
  const raw = Number(localStorage.getItem(SIDEBAR_KEY));
  if (!Number.isFinite(raw)) return SIDEBAR_DEFAULT;
  return Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, raw));
}

export function writeSidebarWidth(width: number): void {
  localStorage.setItem(SIDEBAR_KEY, String(width));
}
