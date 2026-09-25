import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../../environments/environment';
import { VocabularyDetail } from '../models/vocabulary.models';
import { WordOfTheDayService, istDate } from './word-of-the-day.service';

const URL = `${environment.apiUrl}/communication/vocabulary/word-of-the-day`;
const USER = 'user-1';

function wotdWord(overrides: Partial<VocabularyDetail> = {}): VocabularyDetail {
  return {
    id: 'w20260925',
    term: 'herald',
    type: 'WORD',
    level: 'B1',
    part_of_speech: 'noun',
    simple_meaning: 'A messenger bearing news.',
    meaning_in_context: null,
    example: 'The herald announced the king.',
    example_context: null,
    usage_note: null,
    communication_intents: [],
    topics: [],
    common_collocations: [],
    synonyms: ['envoy'],
    antonyms: [],
    commonness: 'common',
    formality: 'neutral',
    pronunciation: null,
    learning_priority: 'medium',
    ...overrides,
  };
}

describe('WordOfTheDayService', () => {
  let service: WordOfTheDayService;
  let http: HttpTestingController;
  const todayKey = `lifeos.wotd.${USER}.${istDate()}`;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(WordOfTheDayService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  it('uses today\'s cached word without calling the API', () => {
    localStorage.setItem(todayKey, JSON.stringify(wotdWord()));
    service.load(USER);
    http.expectNone(URL);
    expect(service.word()?.term).toBe('herald');
  });

  it('fetches, caches for today, and drops older cached days', () => {
    localStorage.setItem(`lifeos.wotd.${USER}.2000-01-01`, JSON.stringify(wotdWord({ term: 'old' })));
    service.load(USER);
    http.expectOne(URL).flush({ connected: true, date: istDate(), vocabulary: wotdWord() });

    expect(service.word()?.term).toBe('herald');
    expect(JSON.parse(localStorage.getItem(todayKey)!).term).toBe('herald');
    expect(localStorage.getItem(`lifeos.wotd.${USER}.2000-01-01`)).toBeNull();
  });

  it('does not cache or show anything when not connected', () => {
    service.load(USER);
    http.expectOne(URL).flush({ connected: false, date: istDate(), vocabulary: null });
    expect(service.word()).toBeNull();
    expect(localStorage.getItem(todayKey)).toBeNull();
  });

  it('ignores a malformed cache entry and refetches', () => {
    localStorage.setItem(todayKey, '{"not":"a word"}');
    service.load(USER);
    http.expectOne(URL).flush({ connected: true, date: istDate(), vocabulary: wotdWord() });
    expect(service.word()?.term).toBe('herald');
  });

  it('clearCache removes only this user\'s entries', () => {
    localStorage.setItem(todayKey, JSON.stringify(wotdWord()));
    localStorage.setItem(`lifeos.wotd.other.${istDate()}`, JSON.stringify(wotdWord()));
    service.clearCache(USER);
    expect(localStorage.getItem(todayKey)).toBeNull();
    expect(localStorage.getItem(`lifeos.wotd.other.${istDate()}`)).not.toBeNull();
  });
});
