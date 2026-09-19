// A practical JSONPath subset: $ . [] [*] [n] .. (recursive descent).
// Does not support filter expressions (e.g. [?(@.x==1)]) or script expressions.

type Step = { type: 'prop'; name: string } | { type: 'index'; index: number } | { type: 'wildcard' } | { type: 'recursive' };

const TOKEN_RE = /\$|\.\.|\.\*|\.[A-Za-z0-9_]+|\[\*\]|\[\d+\]|\['[^']*'\]|\["[^"]*"\]|[A-Za-z0-9_]+/g;

function parsePath(path: string): Step[] {
  const trimmed = path.trim();
  const steps: Step[] = [];
  let matchedLength = 0;
  let match: RegExpExecArray | null;
  TOKEN_RE.lastIndex = 0;
  while ((match = TOKEN_RE.exec(trimmed))) {
    if (match.index !== matchedLength) {
      throw new Error(`Unrecognized JSONPath syntax at position ${matchedLength}.`);
    }
    const tok = match[0];
    matchedLength += tok.length;
    if (tok === '$') continue;
    if (tok === '..') {
      steps.push({ type: 'recursive' });
      continue;
    }
    if (tok === '.*' || tok === '[*]') {
      steps.push({ type: 'wildcard' });
      continue;
    }
    if (tok.startsWith('.')) {
      steps.push({ type: 'prop', name: tok.slice(1) });
      continue;
    }
    if (/^\[\d+\]$/.test(tok)) {
      steps.push({ type: 'index', index: Number(tok.slice(1, -1)) });
      continue;
    }
    if (/^\['.*'\]$/.test(tok) || /^\[".*"\]$/.test(tok)) {
      steps.push({ type: 'prop', name: tok.slice(2, -2) });
      continue;
    }
    steps.push({ type: 'prop', name: tok });
  }
  if (matchedLength !== trimmed.length) {
    throw new Error(`Unrecognized JSONPath syntax at position ${matchedLength}. Supported: $, ., [], [*], [n], .. — not filter expressions.`);
  }
  return steps;
}

function collectRecursive(item: unknown, propName: string, results: unknown[]): void {
  if (item !== null && typeof item === 'object') {
    if (!Array.isArray(item) && propName in item) {
      results.push((item as Record<string, unknown>)[propName]);
    }
    const children = Array.isArray(item) ? item : Object.values(item as object);
    for (const child of children) collectRecursive(child, propName, results);
  }
}

function applySimpleStep(item: unknown, step: Step): unknown[] {
  if (step.type === 'wildcard') {
    if (Array.isArray(item)) return item;
    if (item !== null && typeof item === 'object') return Object.values(item);
    return [];
  }
  if (step.type === 'prop') {
    if (item !== null && typeof item === 'object' && !Array.isArray(item) && step.name in item) {
      return [(item as Record<string, unknown>)[step.name]];
    }
    return [];
  }
  if (step.type === 'index') {
    if (Array.isArray(item) && step.index >= 0 && step.index < item.length) return [item[step.index]];
    return [];
  }
  return [];
}

export function evaluateJsonPath(path: string, data: unknown): unknown[] {
  const steps = parsePath(path);
  let current: unknown[] = [data];
  let i = 0;
  while (i < steps.length) {
    const step = steps[i];
    if (step.type === 'recursive') {
      const next = steps[i + 1];
      if (!next || next.type !== 'prop') {
        throw new Error('".." must be followed by a property name, e.g. "..price".');
      }
      const results: unknown[] = [];
      for (const item of current) collectRecursive(item, next.name, results);
      current = results;
      i += 2;
      continue;
    }
    current = current.flatMap((item) => applySimpleStep(item, step));
    i++;
  }
  return current;
}
