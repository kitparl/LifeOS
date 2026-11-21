import { Injectable } from '@angular/core';
import { SplitOrientation } from '../../../shared/code-workspace/components/editor-toolbar/editor-toolbar.component';
import { DsaLanguage, EDITOR_POSITIONS, EditorPosition } from '../models/dsa.models';

const PREFIX = 'dsa:draft:';
const CASES_PREFIX = 'dsa:cases:';
const LANGUAGE_KEY = 'dsa:language';
/** Description's share per layout: side by side (key kept from before stacked layouts) or stacked. */
const SPLIT_KEYS: Record<SplitOrientation, string> = { horizontal: 'dsa:split', vertical: 'dsa:split-v' };
const POSITION_KEY = 'dsa:editor-position';

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

  /** Description's share of the problem page split (0–1) for that layout, or null if unset/invalid. */
  splitRatio(orientation: SplitOrientation = 'horizontal'): number | null {
    const value = Number(this.read(SPLIT_KEYS[orientation]));
    return Number.isFinite(value) && value > 0 && value < 1 ? value : null;
  }

  rememberSplitRatio(ratio: number, orientation: SplitOrientation = 'horizontal'): void {
    this.write(SPLIT_KEYS[orientation], String(ratio));
  }

  /** Where the editor sits on the problem page, or null if unset/unknown. */
  editorPosition(): EditorPosition | null {
    const value = this.read(POSITION_KEY);
    return EDITOR_POSITIONS.find((p) => p === value) ?? null;
  }

  rememberEditorPosition(position: EditorPosition): void {
    this.write(POSITION_KEY, position);
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
