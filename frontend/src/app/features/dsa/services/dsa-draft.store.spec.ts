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

  it('remembers the last language', () => {
    expect(store.lastLanguage()).toBeNull();
    store.rememberLanguage('cpp');
    expect(store.lastLanguage()).toBe('cpp');
  });

  it('degrades silently when storage throws', () => {
    store.storage = () => {
      throw new Error('blocked');
    };
    expect(() => store.save('a', 'python', 'x')).not.toThrow();
    expect(() => store.clear('a', 'python')).not.toThrow();
    expect(store.load('a', 'python')).toBeNull();
    expect(store.lastLanguage()).toBeNull();
  });
});
