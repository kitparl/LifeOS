export const MAX_MARKDOWN_IMPORT_BYTES = 2 * 1024 * 1024;

export type MarkdownImportAction = 'replace' | 'append';

export function isMarkdownFile(file: File): boolean {
  const name = file.name.toLowerCase();
  const type = (file.type || '').toLowerCase();
  return (
    name.endsWith('.md') ||
    type === 'text/markdown' ||
    type === 'text/plain' ||
    type === ''
  );
}

export function validateMarkdownFile(file: File): string | null {
  if (!isMarkdownFile(file)) {
    return 'Please select a markdown (.md) or plain text file.';
  }
  if (file.size === 0) {
    return 'The selected file is empty.';
  }
  if (file.size > MAX_MARKDOWN_IMPORT_BYTES) {
    return 'File is too large. Maximum size is 2 MB.';
  }
  return null;
}

export async function readMarkdownFile(file: File): Promise<string> {
  return file.text();
}

export function mergeMarkdownContent(
  current: string,
  imported: string,
  action: MarkdownImportAction
): string {
  if (action === 'replace') {
    return imported;
  }
  const trimmed = current.trimEnd();
  if (!trimmed) {
    return imported;
  }
  return `${trimmed}\n\n${imported}`;
}

export function hasMarkdownContent(text: string): boolean {
  return text.trim().length > 0;
}

export function extractFirstHeading(text: string): string | null {
  const match = text.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : null;
}

export function titleFromFilename(filename: string): string | null {
  const base = filename.replace(/\.md$/i, '').trim();
  return base || null;
}

export function suggestTitleFromImport(
  filename: string,
  importedText: string,
  currentTitle: string
): string | null {
  const untitled =
    !currentTitle.trim() || currentTitle.trim().toLowerCase() === 'untitled';
  if (!untitled) {
    return null;
  }
  return extractFirstHeading(importedText) ?? titleFromFilename(filename);
}
