export function formatCss(input: string, indentSize = 2): string {
  const indentUnit = ' '.repeat(indentSize);
  let result = '';
  let depth = 0;
  let i = 0;
  let inString: string | null = null;
  const src = input.replace(/\/\*[\s\S]*?\*\//g, '').trim();
  let buffer = '';
  const flush = (): string => {
    const t = buffer.trim();
    buffer = '';
    return t;
  };
  while (i < src.length) {
    const ch = src[i];
    if (inString) {
      buffer += ch;
      if (ch === inString && src[i - 1] !== '\\') inString = null;
      i++;
      continue;
    }
    if (ch === '"' || ch === "'") {
      inString = ch;
      buffer += ch;
      i++;
      continue;
    }
    if (ch === '{') {
      const selector = flush();
      result += `${indentUnit.repeat(depth)}${selector} {\n`;
      depth++;
      i++;
      continue;
    }
    if (ch === '}') {
      const decl = flush();
      if (decl) result += `${indentUnit.repeat(depth)}${decl};\n`;
      depth = Math.max(0, depth - 1);
      result += `${indentUnit.repeat(depth)}}\n`;
      i++;
      continue;
    }
    if (ch === ';') {
      const decl = flush();
      if (decl) result += `${indentUnit.repeat(depth)}${decl};\n`;
      i++;
      continue;
    }
    buffer += ch;
    i++;
  }
  const trailing = flush();
  if (trailing) result += trailing + '\n';
  return result.trim() + '\n';
}

export function minifyCss(input: string): string {
  return input
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/\s*([{}:;,])\s*/g, '$1')
    .replace(/;}/g, '}')
    .replace(/\s+/g, ' ')
    .trim();
}
