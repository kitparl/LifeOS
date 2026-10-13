import { ContributorMe } from '../models/share.models';

/**
 * What the planner keeps in this browser, per link code. Storage can be missing or blocked
 * (private windows, in-app browsers), so every read and write is guarded and the planner
 * still works without it, just without remembering the friend.
 */

export interface StoredIdentity {
  deviceSecret: string;
  contributor: ContributorMe;
}

export interface StoredToken {
  token: string;
  expiresAt: string;
}

export interface StoredDraft<T> {
  revision: number;
  doc: T;
  savedAt: string;
}

const key = (code: string, suffix = '') => `tp:${code}${suffix}`;

function read<T>(storage: Storage | undefined, k: string): T | null {
  try {
    const raw = storage?.getItem(k);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

function write(storage: Storage | undefined, k: string, value: unknown): void {
  try {
    if (value === null) storage?.removeItem(k);
    else storage?.setItem(k, JSON.stringify(value));
  } catch {
    // Storage full or blocked: the planner keeps working for this visit.
  }
}

const local = () => (typeof localStorage === 'undefined' ? undefined : localStorage);
const session = () => (typeof sessionStorage === 'undefined' ? undefined : sessionStorage);

export const plannerStorage = {
  identity: (code: string) => read<StoredIdentity>(local(), key(code)),
  setIdentity: (code: string, value: StoredIdentity | null) => write(local(), key(code), value),
  token: (code: string) => {
    const stored = read<StoredToken>(session(), key(code, ':token'));
    return stored && Date.parse(stored.expiresAt) - Date.now() > 60_000 ? stored : null;
  },
  setToken: (code: string, value: StoredToken | null) => write(session(), key(code, ':token'), value),
  draft: <T>(code: string) => read<StoredDraft<T>>(local(), key(code, ':draft')),
  setDraft: <T>(code: string, value: StoredDraft<T> | null) => write(local(), key(code, ':draft'), value),
  firstRunDone: () => read<boolean>(local(), 'tp:first-run') === true,
  setFirstRunDone: () => write(local(), 'tp:first-run', true),
};

/** In-app browsers (WhatsApp, Instagram, Facebook, ...) where Google blocks sign-in. */
export function isInAppBrowser(userAgent: string = navigator.userAgent): boolean {
  return /FBAN|FBAV|FB_IAB|Instagram|WhatsApp|Line\/|Snapchat|LinkedInApp|; wv\)/i.test(userAgent);
}
