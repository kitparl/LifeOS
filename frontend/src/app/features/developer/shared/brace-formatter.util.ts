// Lightweight, dependency-free re-indenter for brace/bracket languages (JS/TS/Java/etc.).
// It re-indents existing line breaks by bracket depth rather than fully reflowing the code —
// a deliberate, honest scope for a dependency-free "beautifier" (see execution plan risks).

function fixCurrentLineIndent(out: string, depth: number, indentUnit: string): string {
  const lastNewline = out.lastIndexOf('\n');
  const currentLine = out.slice(lastNewline + 1);
  if (/^[ \t]*$/.test(currentLine)) {
    return out.slice(0, lastNewline + 1) + indentUnit.repeat(depth);
  }
  return out;
}

export function reindentCode(input: string, indentSize = 2): string {
  const indentUnit = ' '.repeat(indentSize);
  let depth = 0;
  let out = '';
  let i = 0;
  let inString: string | null = null;
  let inLineComment = false;
  let inBlockComment = false;
  const n = input.length;

  while (i < n) {
    const ch = input[i];
    const next = input[i + 1];

    if (inLineComment) {
      out += ch;
      if (ch === '\n') inLineComment = false;
      i++;
      continue;
    }
    if (inBlockComment) {
      out += ch;
      if (ch === '*' && next === '/') {
        out += next;
        i += 2;
        inBlockComment = false;
        continue;
      }
      i++;
      continue;
    }
    if (inString) {
      out += ch;
      if (ch === '\\') {
        out += next ?? '';
        i += 2;
        continue;
      }
      if (ch === inString) inString = null;
      i++;
      continue;
    }
    if (ch === '/' && next === '/') {
      inLineComment = true;
      out += ch;
      i++;
      continue;
    }
    if (ch === '/' && next === '*') {
      inBlockComment = true;
      out += ch;
      i++;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') {
      inString = ch;
      out += ch;
      i++;
      continue;
    }
    if (ch === '}' || ch === ')' || ch === ']') {
      depth = Math.max(0, depth - 1);
      out = fixCurrentLineIndent(out, depth, indentUnit);
      out += ch;
      i++;
      continue;
    }
    if (ch === '{' || ch === '(' || ch === '[') {
      out += ch;
      depth++;
      i++;
      continue;
    }
    if (ch === '\n') {
      out += '\n';
      i++;
      while (i < n && (input[i] === ' ' || input[i] === '\t')) i++;
      out += indentUnit.repeat(depth);
      continue;
    }
    out += ch;
    i++;
  }
  return out.trim() + '\n';
}

/** Strips comments and collapses whitespace to single spaces, preserving string/template contents exactly. */
export function minifyCode(input: string): string {
  let out = '';
  let i = 0;
  const n = input.length;
  let inString: string | null = null;
  let inLineComment = false;
  let inBlockComment = false;
  let lastWasSpace = false;

  while (i < n) {
    const ch = input[i];
    const next = input[i + 1];

    if (inLineComment) {
      if (ch === '\n') inLineComment = false;
      i++;
      continue;
    }
    if (inBlockComment) {
      if (ch === '*' && next === '/') {
        inBlockComment = false;
        i += 2;
        continue;
      }
      i++;
      continue;
    }
    if (inString) {
      out += ch;
      lastWasSpace = false;
      if (ch === '\\') {
        out += next ?? '';
        i += 2;
        continue;
      }
      if (ch === inString) inString = null;
      i++;
      continue;
    }
    if (ch === '/' && next === '/') {
      inLineComment = true;
      i += 2;
      continue;
    }
    if (ch === '/' && next === '*') {
      inBlockComment = true;
      i += 2;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') {
      inString = ch;
      out += ch;
      lastWasSpace = false;
      i++;
      continue;
    }
    if (/\s/.test(ch)) {
      if (!lastWasSpace) {
        out += ' ';
        lastWasSpace = true;
      }
      i++;
      continue;
    }
    out += ch;
    lastWasSpace = false;
    i++;
  }
  return out.trim();
}
