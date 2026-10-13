import { Injectable } from '@angular/core';
import { DsaLanguage } from '../models/dsa.models';

const PREFIX = 'dsa:draft:';
const CASES_PREFIX = 'dsa:cases:';
const LANGUAGE_KEY = 'dsa:language';
const SPLIT_KEY = 'dsa:split';

/**
 * Per-browser code drafts (per problem and language), Run test cases (per problem) and the last language used.
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
    this.remove(`${PREFIX}${slug}:${language}`);
  }

  /** Run test cases as edited: one JSON text per input field, per case. Null if unset or malformed. */
  loadCases(slug: string): string[][] | null {
    try {
      const value: unknown = JSON.parse(this.read(`${CASES_PREFIX}${slug}`) ?? 'null');
      const valid = Array.isArray(value) && value.every((c) => Array.isArray(c) && c.every((t) => typeof t === 'string'));
      return valid ? (value as string[][]) : null;
    } catch {
      return null;
    }
  }

  saveCases(slug: string, cases: string[][]): void {
    this.write(`${CASES_PREFIX}${slug}`, JSON.stringify(cases));
  }

  clearCases(slug: string): void {
    this.remove(`${CASES_PREFIX}${slug}`);
  }

  lastLanguage(): DsaLanguage | null {
    return this.read(LANGUAGE_KEY) as DsaLanguage | null;
  }

  rememberLanguage(language: DsaLanguage): void {
    this.write(LANGUAGE_KEY, language);
  }

  /** Description column's share of the problem page split (0–1), or null if unset/invalid. */
  splitRatio(): number | null {
    const value = Number(this.read(SPLIT_KEY));
    return Number.isFinite(value) && value > 0 && value < 1 ? value : null;
  }

  rememberSplitRatio(ratio: number): void {
    this.write(SPLIT_KEY, String(ratio));
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

  private remove(key: string): void {
    try {
      this.storage().removeItem(key);
    } catch {
      /* storage unavailable */
    }
  }
}
