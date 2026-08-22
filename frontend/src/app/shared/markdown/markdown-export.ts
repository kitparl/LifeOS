const UNSAFE_FILENAME_CHARS = /[<>:"/\\|?*\x00-\x1f]/g;

export function sanitizeMarkdownFilename(title: string, fallback = 'export'): string {
  const base = (title.trim() || fallback).replace(UNSAFE_FILENAME_CHARS, '').replace(/\s+/g, '-');
  const trimmed = base.replace(/^-+|-+$/g, '') || fallback;
  return trimmed.toLowerCase().endsWith('.md') ? trimmed : `${trimmed}.md`;
}

export function downloadMarkdown(content: string, filename: string): void {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = sanitizeMarkdownFilename(filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
