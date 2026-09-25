import { InjectionToken } from '@angular/core';

/**
 * Which browser-storage namespace the Developer tools use. Logged-in users keep the original keys
 * ('user'); the public Explore Tools route provides 'guest' so a visitor on the same browser never
 * sees the owner's favorites or history (logout does not clear client-only storage).
 */
export type DevToolsStorageScope = 'user' | 'guest';

export const DEV_TOOLS_STORAGE_SCOPE = new InjectionToken<DevToolsStorageScope>('DEV_TOOLS_STORAGE_SCOPE', {
  providedIn: 'root',
  factory: () => 'user',
});

export function scopedStorageName(base: string, scope: DevToolsStorageScope): string {
  return scope === 'guest' ? `${base}-guest` : base;
}
