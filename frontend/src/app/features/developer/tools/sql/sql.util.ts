const NEWLINE_BEFORE = [
  'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'OFFSET', 'INSERT INTO', 'VALUES',
  'UPDATE', 'SET', 'DELETE FROM', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'FULL JOIN', 'JOIN', 'UNION ALL', 'UNION', 'ON',
].sort((a, b) => b.length - a.length);

/** A lightweight, keyword-based reformatter — not a full SQL parser. Normalizes major keywords to uppercase on their own line. */
export function formatSql(input: string): string {
  let sql = input.replace(/\s+/g, ' ').trim();
  for (const kw of NEWLINE_BEFORE) {
    const re = new RegExp(`\\s+(${kw.replace(/ /g, '\\s+')})\\b`, 'gi');
    sql = sql.replace(re, `\n${kw}`);
  }
  sql = sql.replace(/\s+(AND|OR)\b/gi, '\n  $1');
  return sql
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)
    .join('\n');
}

export function minifySql(input: string): string {
  return input.replace(/\s+/g, ' ').trim();
}

export interface SqlValidationResult {
  valid: boolean;
  issues: string[];
}

/** Heuristic checks only (balanced parens/quotes, starts with a known keyword) — not a full parser. */
export function validateSqlBasic(input: string): SqlValidationResult {
  const issues: string[] = [];
  const trimmed = input.trim();
  if (!trimmed) {
    return { valid: false, issues: ['Statement is empty.'] };
  }
  let parenDepth = 0;
  let inString: string | null = null;
  for (let i = 0; i < trimmed.length; i++) {
    const ch = trimmed[i];
    if (inString) {
      if (ch === inString && trimmed[i - 1] !== '\\') inString = null;
      continue;
    }
    if (ch === "'" || ch === '"') {
      inString = ch;
      continue;
    }
    if (ch === '(') parenDepth++;
    if (ch === ')') {
      parenDepth--;
      if (parenDepth < 0) {
        issues.push(`Unmatched ")" at position ${i}.`);
        parenDepth = 0;
      }
    }
  }
  if (parenDepth > 0) issues.push(`${parenDepth} unclosed "(".`);
  if (inString) issues.push(`Unterminated string literal (missing closing ${inString}).`);
  const startsWithKeyword = /^(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|WITH|TRUNCATE|REPLACE)\b/i.test(trimmed);
  if (!startsWithKeyword) issues.push('Statement does not start with a recognized SQL keyword.');
  return { valid: issues.length === 0, issues };
}

function splitValueGroups(text: string): string[] {
  const groups: string[] = [];
  let depth = 0;
  let current = '';
  let inString: string | null = null;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (inString) {
      current += ch;
      if (ch === inString && text[i - 1] !== '\\') inString = null;
      continue;
    }
    if (ch === "'" || ch === '"') {
      inString = ch;
      current += ch;
      continue;
    }
    if (ch === '(') {
      depth++;
      if (depth === 1) {
        current = '';
        continue;
      }
    }
    if (ch === ')') {
      depth--;
      if (depth === 0) {
        groups.push(current);
        continue;
      }
    }
    if (depth >= 1) current += ch;
  }
  return groups;
}

function splitCsvRespectingQuotes(text: string): string[] {
  const parts: string[] = [];
  let current = '';
  let inString: string | null = null;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (inString) {
      current += ch;
      if (ch === inString && text[i - 1] !== '\\') inString = null;
      continue;
    }
    if (ch === "'" || ch === '"') {
      inString = ch;
      current += ch;
      continue;
    }
    if (ch === ',') {
      parts.push(current.trim());
      current = '';
      continue;
    }
    current += ch;
  }
  parts.push(current.trim());
  return parts;
}

function parseSqlLiteral(raw: string | undefined): unknown {
  if (raw === undefined) return null;
  const t = raw.trim();
  if (/^null$/i.test(t)) return null;
  if (/^-?\d+(\.\d+)?$/.test(t)) return Number(t);
  if (/^true$/i.test(t)) return true;
  if (/^false$/i.test(t)) return false;
  if ((t.startsWith("'") && t.endsWith("'")) || (t.startsWith('"') && t.endsWith('"'))) {
    return t.slice(1, -1).replace(/''/g, "'");
  }
  return t;
}

/** Converts a simple `INSERT INTO table (col1, col2) VALUES (...), (...)` statement into a JSON array of objects. */
export function sqlInsertToJson(sql: string): unknown[] {
  const match = sql.match(/INSERT\s+INTO\s+[`"[]?\w+[`"\]]?\s*\(([^)]+)\)\s*VALUES\s*(.+?);?\s*$/is);
  if (!match) {
    throw new Error('Expected an "INSERT INTO table (col1, col2) VALUES (...), (...)" statement.');
  }
  const columns = match[1].split(',').map((c) => c.trim().replace(/^[`"[]|[`"\]]$/g, ''));
  const rows = splitValueGroups(match[2]);
  if (rows.length === 0) {
    throw new Error('No value groups found after VALUES.');
  }
  return rows.map((row) => {
    const values = splitCsvRespectingQuotes(row);
    const obj: Record<string, unknown> = {};
    columns.forEach((col, i) => {
      obj[col] = parseSqlLiteral(values[i]);
    });
    return obj;
  });
}
