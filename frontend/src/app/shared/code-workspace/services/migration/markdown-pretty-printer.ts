/**
 * Formats Markdown into a stable normal form (idempotent).
 * Requirements 22.1–22.6.
 */
export function prettyPrintMarkdown(markdown: string): string {
  if (!markdown || !markdown.trim()) {
    return '';
  }

  const fences: string[] = [];
  let text = markdown.replace(/\r\n/g, '\n');
  text = text.replace(/```[\s\S]*?```/g, (block) => {
    fences.push(block.replace(/[ \t]+$/gm, '').trimEnd());
    return `\n\n@@FENCE${fences.length - 1}@@\n\n`;
  });

  text = normalizeLinksAndImages(text);

  const lines = text.split('\n').map((line) => line.replace(/[ \t]+$/, ''));
  const blocks = toBlocks(lines);
  const formatted = blocks.map(formatBlock).filter((block) => block.length > 0).join('\n\n');

  const restored = formatted.replace(/@@FENCE(\d+)@@/g, (_match, index: string) => {
    return fences[Number(index)] ?? '';
  });

  return `${restored.replace(/\n{3,}/g, '\n\n').trim()}\n`;
}

function toBlocks(lines: string[]): string[][] {
  const blocks: string[][] = [];
  let current: string[] = [];
  let kind: BlockKind | null = null;

  const flush = (): void => {
    if (current.length) {
      blocks.push(current);
      current = [];
      kind = null;
    }
  };

  for (const line of lines) {
    const next = classify(line);
    if (next === 'blank') {
      flush();
      continue;
    }
    if (kind && next !== kind && !canJoin(kind, next, line)) {
      flush();
    }
    kind = kind ?? next;
    current.push(line);
  }
  flush();
  return blocks;
}

type BlockKind = 'heading' | 'list' | 'quote' | 'hr' | 'fence' | 'para';

function classify(line: string): BlockKind | 'blank' {
  if (!line.trim()) {
    return 'blank';
  }
  if (/^@@FENCE\d+@@$/.test(line.trim())) {
    return 'fence';
  }
  if (/^#{1,6}\s+\S/.test(line) || /^#{1,6}$/.test(line.trim())) {
    return 'heading';
  }
  if (/^\s*([-*+]|\d+\.)\s+/.test(line)) {
    return 'list';
  }
  if (/^\s*>/.test(line)) {
    return 'quote';
  }
  if (/^(\*{3,}|-{3,}|_{3,})$/.test(line.trim())) {
    return 'hr';
  }
  return 'para';
}

function canJoin(kind: BlockKind, next: BlockKind, line: string): boolean {
  if (kind === next) {
    return kind === 'list' || kind === 'quote' || kind === 'para';
  }
  return kind === 'list' && next === 'para' && /^\s+\S/.test(line);
}

function formatBlock(lines: string[]): string {
  const kind = classify(lines[0]);
  switch (kind) {
    case 'heading':
      return formatHeading(lines[0]);
    case 'list':
      return formatList(lines);
    case 'quote':
      return formatQuote(lines);
    case 'hr':
      return '---';
    case 'fence':
      return lines[0].trim();
    default:
      return lines.join('\n').trim();
  }
}

function formatHeading(line: string): string {
  const match = line.trim().match(/^(#{1,6})\s*(.*)$/);
  if (!match) {
    return line.trim();
  }
  const title = match[2].trim();
  return title ? `${match[1]} ${title}` : match[1];
}

function formatList(lines: string[]): string {
  const indents = lines
    .map((line) => {
      const match = line.match(/^(\s*)([-*+]|\d+\.)\s+/);
      return match ? expandTabs(match[1]).length : -1;
    })
    .filter((value) => value >= 0);

  const unit = indentUnit(indents);

  return lines
    .map((line) => {
      const match = line.match(/^(\s*)([-*+]|\d+\.)\s+(.*)$/);
      if (!match) {
        const leading = expandTabs(line.match(/^(\s*)/)?.[1] || '').length;
        const level = nestLevel(leading, unit);
        return `${'  '.repeat(level)}${line.trim()}`;
      }
      const spaces = expandTabs(match[1]).length;
      const level = nestLevel(spaces, unit);
      const marker = /^\d+\./.test(match[2]) ? match[2] : '-';
      return `${'  '.repeat(level)}${marker} ${match[3].trim()}`;
    })
    .join('\n');
}

function formatQuote(lines: string[]): string {
  return lines
    .map((line) => {
      const body = line.replace(/^\s*>\s?/, '').trimEnd();
      return body ? `> ${body}` : '>';
    })
    .join('\n');
}

function expandTabs(value: string): string {
  return value.replace(/\t/g, '  ');
}

function indentUnit(indents: number[]): number {
  const nested = indents.filter((value) => value > 0);
  if (!nested.length) {
    return 2;
  }
  const unit = nested.reduce((a, b) => gcd(a, b));
  if (unit >= 4) {
    return 4;
  }
  return 2;
}

function nestLevel(spaces: number, unit: number): number {
  if (spaces <= 0) {
    return 0;
  }
  return Math.max(1, Math.round(spaces / unit));
}

function gcd(a: number, b: number): number {
  let x = Math.abs(a);
  let y = Math.abs(b);
  while (y) {
    const next = x % y;
    x = y;
    y = next;
  }
  return x || 2;
}

function normalizeLinksAndImages(markdown: string): string {
  const existing = new Map<string, string>();
  const defPattern = /^\[([^\]]+)\]:\s+(\S+)\s*$/gm;
  let defMatch: RegExpExecArray | null;
  while ((defMatch = defPattern.exec(markdown))) {
    existing.set(defMatch[2], defMatch[1]);
  }

  const inlinePattern = /(!?)\[([^\]]*)\]\(([^)]+)\)/g;
  const urls: string[] = [];
  let inlineMatch: RegExpExecArray | null;
  const scanner = new RegExp(inlinePattern.source, 'g');
  while ((inlineMatch = scanner.exec(markdown))) {
    urls.push(inlineMatch[3].trim());
  }

  const frequency = new Map<string, number>();
  for (const url of urls) {
    frequency.set(url, (frequency.get(url) || 0) + 1);
  }

  const usedIds = new Set(existing.values());
  const newDefs: Array<{ id: string; url: string }> = [];

  const rewritten = markdown.replace(inlinePattern, (full, bang: string, text: string, rawUrl: string) => {
    const url = rawUrl.trim();
    if (!shouldUseReferenceStyle(url, frequency.get(url) || 0)) {
      return full;
    }

    let id = existing.get(url);
    if (!id) {
      id = toRefId(url, usedIds);
      existing.set(url, id);
      newDefs.push({ id, url });
    }
    return `${bang}[${text}][${id}]`;
  });

  if (!newDefs.length) {
    return rewritten;
  }

  const defs = newDefs.map((def) => `[${def.id}]: ${def.url}`).join('\n');
  return `${rewritten.trimEnd()}\n\n${defs}\n`;
}

function shouldUseReferenceStyle(url: string, count: number): boolean {
  if (url.startsWith('#') && url.length < 40) {
    return false;
  }
  return count > 1 || url.length >= 40;
}

function toRefId(url: string, used: Set<string>): string {
  let base = url
    .replace(/^https?:\/\//i, '')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40)
    .toLowerCase();
  if (!base) {
    base = 'ref';
  }
  let id = base;
  let n = 2;
  while (used.has(id)) {
    id = `${base}-${n++}`;
  }
  used.add(id);
  return id;
}
