// A pragmatic YAML subset: block mappings/sequences, flow collections ([...]/{...} via JSON),
// quoted/unquoted scalars, and # comments. Not the full YAML spec — no anchors, tags, multi-doc,
// or block scalars (|, >). Sufficient for JSON-equivalent structured data, which is this module's scope.

interface YamlLine {
  indent: number;
  content: string;
}

function tokenize(text: string): YamlLine[] {
  return text
    .split('\n')
    .map((raw) => raw.replace(/\r$/, ''))
    .filter((line) => line.trim() !== '' && !/^\s*#/.test(line))
    .map((line) => ({ indent: line.match(/^ */)![0].length, content: line.trim() }));
}

export function parseYaml(text: string): unknown {
  const lines = tokenize(text);
  if (lines.length === 0) return null;
  try {
    const [value] = parseBlock(lines, 0, lines[0].indent);
    return value;
  } catch (e) {
    throw new Error(`Invalid YAML: ${e instanceof Error ? e.message : String(e)}`);
  }
}

function parseBlock(lines: YamlLine[], startIdx: number, indent: number): [unknown, number] {
  if (startIdx >= lines.length) return [null, startIdx];
  const first = lines[startIdx];
  if (first.indent !== indent) {
    throw new Error(`unexpected indentation near "${first.content}"`);
  }
  if (first.content === '-' || first.content.startsWith('- ')) {
    return parseSequence(lines, startIdx, indent);
  }
  if (/^("[^"]*"|'[^']*'|[^:]+):\s*(.*)$/.test(first.content)) {
    return parseMapping(lines, startIdx, indent);
  }
  return [parseScalar(first.content), startIdx + 1];
}

function parseSequence(lines: YamlLine[], startIdx: number, indent: number): [unknown[], number] {
  const result: unknown[] = [];
  let i = startIdx;
  while (i < lines.length && lines[i].indent === indent && (lines[i].content === '-' || lines[i].content.startsWith('- '))) {
    const rest = lines[i].content === '-' ? '' : lines[i].content.slice(2);
    if (rest === '') {
      if (i + 1 < lines.length && lines[i + 1].indent > indent) {
        const [val, next] = parseBlock(lines, i + 1, lines[i + 1].indent);
        result.push(val);
        i = next;
      } else {
        result.push(null);
        i++;
      }
    } else if (/^("[^"]*"|'[^']*'|[^:]+):\s*(.*)$/.test(rest)) {
      const virtualIndent = indent + 2;
      const virtualLines: YamlLine[] = [{ indent: virtualIndent, content: rest }];
      let j = i + 1;
      while (j < lines.length && lines[j].indent >= virtualIndent) {
        virtualLines.push(lines[j]);
        j++;
      }
      const [val] = parseBlock(virtualLines, 0, virtualIndent);
      result.push(val);
      i = j;
    } else {
      result.push(parseScalar(rest));
      i++;
    }
  }
  return [result, i];
}

function parseMapping(lines: YamlLine[], startIdx: number, indent: number): [Record<string, unknown>, number] {
  const result: Record<string, unknown> = {};
  let i = startIdx;
  while (i < lines.length && lines[i].indent === indent && lines[i].content !== '-' && !lines[i].content.startsWith('- ')) {
    const match = lines[i].content.match(/^("[^"]*"|'[^']*'|[^:]+):\s*(.*)$/);
    if (!match) throw new Error(`could not parse line "${lines[i].content}"`);
    const key = parseKey(match[1]);
    const rawValue = match[2];
    if (rawValue === '') {
      if (i + 1 < lines.length && lines[i + 1].indent > indent) {
        const [val, next] = parseBlock(lines, i + 1, lines[i + 1].indent);
        result[key] = val;
        i = next;
      } else {
        result[key] = null;
        i++;
      }
    } else {
      result[key] = parseScalar(rawValue);
      i++;
    }
  }
  return [result, i];
}

function parseKey(raw: string): string {
  const trimmed = raw.trim();
  if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}

function parseScalar(raw: string): unknown {
  const trimmed = raw.trim();
  if (trimmed === '' || trimmed === '~' || trimmed === 'null') return null;
  if (trimmed === 'true') return true;
  if (trimmed === 'false') return false;
  if (/^-?\d+$/.test(trimmed)) return parseInt(trimmed, 10);
  if (/^-?\d+\.\d+$/.test(trimmed)) return parseFloat(trimmed);
  if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
    try {
      return JSON.parse(trimmed);
    } catch {
      throw new Error(`malformed quoted string "${trimmed}"`);
    }
  }
  if (trimmed.startsWith("'") && trimmed.endsWith("'")) {
    return trimmed.slice(1, -1).replace(/''/g, "'");
  }
  if ((trimmed.startsWith('[') && trimmed.endsWith(']')) || (trimmed.startsWith('{') && trimmed.endsWith('}'))) {
    try {
      return JSON.parse(trimmed);
    } catch {
      throw new Error(`malformed inline flow value "${trimmed}"`);
    }
  }
  return trimmed.replace(/\s+#.*$/, '');
}

// --- Stringify (JSON value -> YAML) ---

export function stringifyYaml(value: unknown, indent = 2): string {
  const text = stringifyValue(value, 0, indent);
  return text.endsWith('\n') ? text : text + '\n';
}

function stringifyValue(value: unknown, depth: number, indent: number): string {
  const pad = ' '.repeat(depth * indent);
  if (Array.isArray(value)) {
    if (value.length === 0) return pad + '[]\n';
    return value.map((item) => stringifyArrayItem(item, depth, indent)).join('');
  }
  if (value !== null && typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>);
    if (entries.length === 0) return pad + '{}\n';
    return entries.map(([k, v]) => stringifyEntry(k, v, depth, indent)).join('');
  }
  return pad + scalarToYaml(value) + '\n';
}

function isComplex(value: unknown): boolean {
  if (value === null || typeof value !== 'object') return false;
  return Array.isArray(value) ? value.length > 0 : Object.keys(value).length > 0;
}

function stringifyEntry(key: string, value: unknown, depth: number, indent: number): string {
  const pad = ' '.repeat(depth * indent);
  const safeKey = /^[A-Za-z0-9_.-]+$/.test(key) ? key : JSON.stringify(key);
  if (isComplex(value)) {
    return pad + safeKey + ':\n' + stringifyValue(value, depth + 1, indent);
  }
  return pad + safeKey + ': ' + scalarToYaml(value) + '\n';
}

function stringifyArrayItem(item: unknown, depth: number, indent: number): string {
  const pad = ' '.repeat(depth * indent);
  const dashPrefix = pad + '-' + ' '.repeat(Math.max(1, indent - 1));
  const childIndent = (depth + 1) * indent;

  if (item !== null && typeof item === 'object' && !Array.isArray(item)) {
    const entries = Object.entries(item as Record<string, unknown>);
    if (entries.length === 0) return pad + '- {}\n';
    const mappingText = entries.map(([k, v]) => stringifyEntry(k, v, depth + 1, indent)).join('');
    return spliceDash(mappingText, childIndent, dashPrefix);
  }
  if (Array.isArray(item)) {
    if (item.length === 0) return pad + '- []\n';
    const seqText = stringifyValue(item, depth + 1, indent);
    return spliceDash(seqText, childIndent, dashPrefix);
  }
  return pad + '- ' + scalarToYaml(item) + '\n';
}

function spliceDash(text: string, childIndent: number, dashPrefix: string): string {
  const lines = text.split('\n');
  lines[0] = dashPrefix + lines[0].slice(childIndent);
  return lines.join('\n');
}

function scalarToYaml(value: unknown): string {
  if (value === null || value === undefined) return 'null';
  if (typeof value === 'boolean' || typeof value === 'number') return String(value);
  const text = String(value);
  if (
    text === '' ||
    text === 'true' ||
    text === 'false' ||
    text === 'null' ||
    text === '~' ||
    /^-?\d+(\.\d+)?$/.test(text) ||
    /[:#{}[\],&*!|>'"%@`]/.test(text) ||
    /^\s|\s$/.test(text)
  ) {
    return JSON.stringify(text);
  }
  return text;
}
