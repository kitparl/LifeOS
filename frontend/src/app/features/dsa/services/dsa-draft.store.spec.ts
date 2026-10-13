import { TestBed } from '@angular/core/testing';
import { DsaDraftStore } from './dsa-draft.store';

describe('DsaDraftStore', () => {
  let store: DsaDraftStore;
  let data: Map<string, string>;

  beforeEach(() => {
    store = TestBed.inject(DsaDraftStore);
    data = new Map();
    store.storage = () =>
      ({
        getItem: (k: string) => data.get(k) ?? null,
        setItem: (k: string, v: string) => void data.set(k, v),
        removeItem: (k: string) => void data.delete(k),
      }) as unknown as Storage;
  });

  it('keeps drafts per problem and language', () => {
    store.save('two-sum', 'python', 'py code');
    store.save('two-sum', 'java', 'java code');
    expect(store.load('two-sum', 'python')).toBe('py code');
    expect(store.load('two-sum', 'java')).toBe('java code');
    expect(store.load('other', 'python')).toBeNull();
    store.clear('two-sum', 'python');
    expect(store.load('two-sum', 'python')).toBeNull();
  });

  it('keeps Run test cases per problem and ignores malformed ones', () => {
    expect(store.loadCases('two-sum')).toBeNull();
    store.saveCases('two-sum', [['[1,2]', '3']]);
    expect(store.loadCases('two-sum')).toEqual([['[1,2]', '3']]);
    data.set('dsa:cases:bad', '[[1]]');
    expect(store.loadCases('bad')).toBeNull();
    data.set('dsa:cases:broken', '[[');
    expect(store.loadCases('broken')).toBeNull();
    store.clearCases('two-sum');
    expect(store.loadCases('two-sum')).toBeNull();
  });

  it('remembers the last language', () => {
    expect(store.lastLanguage()).toBeNull();
    store.rememberLanguage('cpp');
    expect(store.lastLanguage()).toBe('cpp');
  });

  it('remembers the split ratio and ignores invalid values', () => {
    expect(store.splitRatio()).toBeNull();
    store.rememberSplitRatio(0.4);
    expect(store.splitRatio()).toBe(0.4);
    store.storage().setItem('dsa:split', 'abc');
    expect(store.splitRatio()).toBeNull();
  });

  it('degrades silently when storage throws', () => {
    store.storage = () => {
      throw new Error('blocked');
    };
    expect(() => store.save('a', 'python', 'x')).not.toThrow();
    expect(() => store.clear('a', 'python')).not.toThrow();
    expect(store.load('a', 'python')).toBeNull();
    expect(store.lastLanguage()).toBeNull();
    expect(store.splitRatio()).toBeNull();
  });
});
