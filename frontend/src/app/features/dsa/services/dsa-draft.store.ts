import { Injectable } from '@angular/core';
import { DsaLanguage } from '../models/dsa.models';

const PREFIX = 'dsa:draft:';
const LANGUAGE_KEY = 'dsa:language';

/**
 * Per-browser code drafts (per problem and language) and the last language used.
 * A convenience only: every storage access may throw (private mode, blocked storage) and then
 * silently does nothing.
 */
@Injectable({ providedIn: 'root' })
export class DsaDraftStore {
  /** Storage seam for tests. */
  storage: () => Storage = () => localStorage;

  load(slug: string, language: DsaLanguage): string | null {
    return this.read(`${PREFIX}${slug}:${language}`);
  }

  save(slug: string, language: DsaLanguage, code: string): void {
    this.write(`${PREFIX}${slug}:${language}`, code);
  }

  clear(slug: string, language: DsaLanguage): void {
    try {
      this.storage().removeItem(`${PREFIX}${slug}:${language}`);
    } catch {
      /* storage unavailable */
    }
  }

  lastLanguage(): DsaLanguage | null {
    return this.read(LANGUAGE_KEY) as DsaLanguage | null;
  }

  rememberLanguage(language: DsaLanguage): void {
    this.write(LANGUAGE_KEY, language);
  }

  private read(key: string): string | null {
    try {
      return this.storage().getItem(key);
    } catch {
      return null;
    }
  }

  private write(key: string, value: string): void {
    try {
      this.storage().setItem(key, value);
    } catch {
      /* storage unavailable or full */
    }
  }
}
