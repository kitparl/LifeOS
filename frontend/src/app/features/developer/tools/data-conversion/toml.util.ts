// A pragmatic TOML subset: tables, array-of-tables, and string/number/bool/array scalars.
// No dates, inline tables, or multi-line strings — sufficient for JSON-equivalent structured data.

function tomlScalar(v: unknown): string {
  if (v === null || v === undefined) return '""';
  if (typeof v === 'boolean' || typeof v === 'number') return String(v);
  if (Array.isArray(v)) return `[${v.map(tomlScalar).join(', ')}]`;
  return JSON.stringify(String(v));
}

function stringifyTomlObject(obj: Record<string, unknown>, path: string[]): string {
  const scalarLines: string[] = [];
  const tableBlocks: string[] = [];
  for (const [k, v] of Object.entries(obj)) {
    if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
      tableBlocks.push(stringifyTomlObject(v as Record<string, unknown>, [...path, k]));
    } else if (Array.isArray(v) && v.some((item) => item !== null && typeof item === 'object')) {
      for (const item of v) {
        tableBlocks.push(`[[${[...path, k].join('.')}]]\n` + stringifyTomlObject(item as Record<string, unknown>, [...path, k]));
      }
    } else {
      scalarLines.push(`${k} = ${tomlScalar(v)}`);
    }
  }
  const header = path.length ? `[${path.join('.')}]\n` : '';
  const body = scalarLines.join('\n') + (scalarLines.length ? '\n' : '');
  return header + body + (tableBlocks.length ? '\n' + tableBlocks.join('\n') : '');
}

export function jsonToToml(value: unknown): string {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('Root JSON value must be an object for TOML output.');
  }
  return stringifyTomlObject(value as Record<string, unknown>, []).trim() + '\n';
}

function splitTomlArrayItems(inner: string): string[] {
  const items: string[] = [];
  let depth = 0;
  let current = '';
  let inString = false;
  for (const ch of inner) {
    if (ch === '"') inString = !inString;
    if (!inString) {
      if (ch === '[') depth++;
      if (ch === ']') depth--;
    }
    if (ch === ',' && depth === 0 && !inString) {
      items.push(current.trim());
      current = '';
      continue;
    }
    current += ch;
  }
  if (current.trim()) items.push(current.trim());
  return items;
}

function parseTomlValue(raw: string): unknown {
  if (raw === 'true') return true;
  if (raw === 'false') return false;
  if (/^-?\d+$/.test(raw)) return Number(raw);
  if (/^-?\d+\.\d+$/.test(raw)) return Number(raw);
  if (raw.startsWith('"') && raw.endsWith('"')) {
    try {
      return JSON.parse(raw);
    } catch {
      throw new Error(`Malformed TOML string: ${raw}`);
    }
  }
  if (raw.startsWith('[') && raw.endsWith(']')) {
    const inner = raw.slice(1, -1).trim();
    return inner ? splitTomlArrayItems(inner).map(parseTomlValue) : [];
  }
  throw new Error(`Unrecognized TOML value: "${raw}" (dates and inline tables are not supported).`);
}

function ensureTable(root: Record<string, unknown>, path: string[]): Record<string, unknown> {
  let obj = root;
  for (const key of path) {
    if (!(key in obj) || typeof obj[key] !== 'object') obj[key] = {};
    obj = obj[key] as Record<string, unknown>;
  }
  return obj;
}

function ensureArrayTable(root: Record<string, unknown>, path: string[]): Record<string, unknown>[] {
  let obj = root;
  for (let i = 0; i < path.length - 1; i++) {
    const key = path[i];
    if (!(key in obj) || typeof obj[key] !== 'object') obj[key] = {};
    obj = obj[key] as Record<string, unknown>;
  }
  const last = path[path.length - 1];
  if (!Array.isArray(obj[last])) obj[last] = [];
  return obj[last] as Record<string, unknown>[];
}

export function tomlToJson(toml: string): unknown {
  const root: Record<string, unknown> = {};
  let current: Record<string, unknown> = root;
  const lines = toml
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith('#'));
  for (const line of lines) {
    const arrayTableMatch = line.match(/^\[\[([^\]]+)]]$/);
    if (arrayTableMatch) {
      const path = arrayTableMatch[1].split('.').map((s) => s.trim());
      const arr = ensureArrayTable(root, path);
      const newObj: Record<string, unknown> = {};
      arr.push(newObj);
      current = newObj;
      continue;
    }
    const tableMatch = line.match(/^\[([^\]]+)]$/);
    if (tableMatch) {
      const path = tableMatch[1].split('.').map((s) => s.trim());
      current = ensureTable(root, path);
      continue;
    }
    const kv = line.match(/^([\w.-]+)\s*=\s*(.+)$/);
    if (!kv) throw new Error(`Could not parse TOML line: "${line}"`);
    current[kv[1]] = parseTomlValue(kv[2].trim());
  }
  return root;
}
