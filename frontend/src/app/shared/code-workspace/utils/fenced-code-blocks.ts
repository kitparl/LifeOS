export interface ParsedCodeBlock {
  id: string;
  language: string;
  code: string;
  lineStart: number;
  lineEnd: number;
}

/** Spec regex: language fence + body, whitespace preserved. */
export const FENCED_CODE_BLOCK_RE = /```(\w+)\n([\s\S]*?)```/g;

const LANGUAGE_ALIASES: Record<string, string> = {
  js: 'javascript',
  ts: 'typescript',
  py: 'python',
};

const EXECUTABLE_LANGUAGES = new Set([
  'javascript',
  'typescript',
  'python',
  'sql',
  'js',
  'ts',
  'py',
]);

export function parseFencedCodeBlocks(markdown: string): ParsedCodeBlock[] {
  const blocks: ParsedCodeBlock[] = [];
  const re = new RegExp(FENCED_CODE_BLOCK_RE.source, FENCED_CODE_BLOCK_RE.flags);
  let match: RegExpExecArray | null;

  while ((match = re.exec(markdown)) !== null) {
    const language = match[1];
    const code = match[2];
    const before = markdown.slice(0, match.index);
    const lineStart = before.split('\n').length;
    const codeLineCount = code.length === 0 ? 1 : code.split('\n').length;
    const lineEnd = lineStart + codeLineCount + 1;

    blocks.push({
      id: `block_${blocks.length}_${match.index}`,
      language,
      code,
      lineStart,
      lineEnd,
    });
  }

  return blocks;
}

export function normalizeExecutableLanguage(language: string): string {
  const key = language.toLowerCase();
  return LANGUAGE_ALIASES[key] ?? key;
}

export function isExecutableLanguage(language: string): boolean {
  return EXECUTABLE_LANGUAGES.has(language.toLowerCase());
}
