import { Injectable, inject, signal } from '@angular/core';
import { VocabularyDetail } from '../models/vocabulary.models';
import { VocabularyService } from './vocabulary.service';

const CACHE_PREFIX = 'lifeos.wotd.';
const IST_DATE_FORMAT = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Kolkata',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});

/** Today's date in IST as YYYY-MM-DD — the same day boundary the backend uses. */
export function istDate(now: Date = new Date()): string {
  return IST_DATE_FORMAT.format(now);
}

function userPrefix(userId: string): string {
  return `${CACHE_PREFIX}${userId}.`;
}

function isVocabularyDetail(value: unknown): value is VocabularyDetail {
  const v = value as Partial<VocabularyDetail> | null;
  return !!v && typeof v.id === 'string' && typeof v.term === 'string' && typeof v.simple_meaning === 'string';
}

/**
 * Word of the Day for the app header. Cache cascade: localStorage for today's IST date
 * (per user) → backend (which serves its DB row, or fetches from Wordnik once per day).
 * Only a connected result with a word is cached, so a disconnected user never sees one.
 */
@Injectable({ providedIn: 'root' })
export class WordOfTheDayService {
  private readonly vocabulary = inject(VocabularyService);

  readonly word = signal<VocabularyDetail | null>(null);

  load(userId: string): void {
    const cached = this.read(userId);
    if (cached) {
      this.word.set(cached);
      return;
    }
    this.vocabulary.wordOfTheDay().subscribe({
      next: (res) => {
        if (res.connected && res.vocabulary) {
          this.write(userId, res.date, res.vocabulary);
          this.word.set(res.vocabulary);
        } else {
          this.word.set(null);
        }
      },
      error: () => this.word.set(null),
    });
  }

  /** Forget cached words for this user (e.g. after the Wordnik key is removed). */
  clearCache(userId: string): void {
    this.word.set(null);
    this.removeKeys(userPrefix(userId));
  }

  private read(userId: string): VocabularyDetail | null {
    try {
      const raw = localStorage.getItem(`${userPrefix(userId)}${istDate()}`);
      const parsed: unknown = raw ? JSON.parse(raw) : null;
      return isVocabularyDetail(parsed) ? parsed : null;
    } catch {
      return null;
    }
  }

  private write(userId: string, date: string, word: VocabularyDetail): void {
    try {
      this.removeKeys(userPrefix(userId));
      localStorage.setItem(`${userPrefix(userId)}${date}`, JSON.stringify(word));
    } catch {
      // Storage unavailable (private mode, quota): the chip still works from the API.
    }
  }

  private removeKeys(prefix: string): void {
    try {
      const stale: string[] = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith(prefix)) stale.push(key);
      }
      stale.forEach((key) => localStorage.removeItem(key));
    } catch {
      // Storage unavailable: nothing to clear.
    }
  }
}
