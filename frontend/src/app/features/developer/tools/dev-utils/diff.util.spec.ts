import { diffLines, computeDiffRows, toUnifiedDiff } from './diff.util';

describe('diff.util', () => {
  it('reports no differences for identical text', () => {
    expect(diffLines('a\nb', 'a\nb').every((l) => l.type === 'unchanged')).toBe(true);
  });

  it('detects added and removed lines', () => {
    const rows = diffLines('a\nb\nc', 'a\nc\nd');
    expect(rows.some((r) => r.type === 'removed' && r.text === 'b')).toBe(true);
    expect(rows.some((r) => r.type === 'added' && r.text === 'd')).toBe(true);
    expect(rows.filter((r) => r.type === 'unchanged').map((r) => r.text)).toEqual(['a', 'c']);
  });

  it('pairs an adjacent removed+added line into a single "changed" row', () => {
    const rows = computeDiffRows('hello world', 'hello there');
    expect(rows.some((r) => r.type === 'changed' && r.left === 'hello world' && r.right === 'hello there')).toBe(true);
  });

  it('produces a unified diff with +/- prefixes', () => {
    const unified = toUnifiedDiff('a\nb', 'a\nc');
    expect(unified).toContain('  a');
    expect(unified).toContain('- b');
    expect(unified).toContain('+ c');
  });
});
