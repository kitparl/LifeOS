import { COPY, FORBIDDEN_WORDS, QUICK_CHIPS } from './planner-copy';

/** Every string in the copy, with sample values for the ones that take a name or number. */
function allText(value: unknown): string[] {
  if (typeof value === 'string') return [value];
  if (typeof value === 'function') return [String((value as (...args: unknown[]) => unknown)('Priya', 2))];
  if (Array.isArray(value)) return value.flatMap(allText);
  if (value && typeof value === 'object') return Object.values(value).flatMap(allText);
  return [];
}

describe('planner copy', () => {
  it('uses plain words only: never version, revision, draft or itinerary item', () => {
    const text = [...allText(COPY), ...allText(QUICK_CHIPS)].join(' \n ').toLowerCase();
    for (const word of FORBIDDEN_WORDS) {
      expect(text).withContext(word).not.toContain(word);
    }
  });

  it('speaks to the friend about the owner by name', () => {
    expect(COPY.sendTo('Priya')).toBe('Send to Priya');
    expect(COPY.privacy('Priya')).toBe('Priya will see your name and Gmail.');
  });
});
