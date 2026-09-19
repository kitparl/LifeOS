export interface JsonDiffEntry {
  path: string;
  type: 'added' | 'removed' | 'changed';
  oldValue?: unknown;
  newValue?: unknown;
}

export function diffJson(a: unknown, b: unknown, path = '$'): JsonDiffEntry[] {
  if (a === b) return [];
  const entries: JsonDiffEntry[] = [];
  const aIsObj = a !== null && typeof a === 'object';
  const bIsObj = b !== null && typeof b === 'object';

  if (aIsObj && bIsObj && Array.isArray(a) === Array.isArray(b)) {
    if (Array.isArray(a) && Array.isArray(b)) {
      const len = Math.max(a.length, b.length);
      for (let i = 0; i < len; i++) {
        const p = `${path}[${i}]`;
        if (i >= a.length) entries.push({ path: p, type: 'added', newValue: b[i] });
        else if (i >= b.length) entries.push({ path: p, type: 'removed', oldValue: a[i] });
        else entries.push(...diffJson(a[i], b[i], p));
      }
    } else {
      const aRecord = a as Record<string, unknown>;
      const bRecord = b as Record<string, unknown>;
      const allKeys = Array.from(new Set([...Object.keys(aRecord), ...Object.keys(bRecord)]));
      for (const key of allKeys) {
        const p = `${path}.${key}`;
        const inA = key in aRecord;
        const inB = key in bRecord;
        if (!inA) entries.push({ path: p, type: 'added', newValue: bRecord[key] });
        else if (!inB) entries.push({ path: p, type: 'removed', oldValue: aRecord[key] });
        else entries.push(...diffJson(aRecord[key], bRecord[key], p));
      }
    }
  } else {
    entries.push({ path, type: 'changed', oldValue: a, newValue: b });
  }
  return entries;
}
