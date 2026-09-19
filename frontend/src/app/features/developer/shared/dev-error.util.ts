/** Turns a native JSON.parse/DOMParser SyntaxError message into a human-readable, positioned error. */
export function formatJsonParseError(input: string, err: unknown): string {
  const message = err instanceof Error ? err.message : String(err);
  const posMatch = message.match(/position (\d+)/i);
  if (!posMatch) return `Invalid JSON: ${message}`;
  const pos = Number(posMatch[1]);
  const { line, column } = lineColumnAt(input, pos);
  return `Invalid JSON at line ${line}, column ${column}. ${cleanMessage(message)}`;
}

export function lineColumnAt(input: string, pos: number): { line: number; column: number } {
  const upto = input.slice(0, Math.max(0, pos));
  const lines = upto.split('\n');
  return { line: lines.length, column: lines[lines.length - 1].length + 1 };
}

function cleanMessage(message: string): string {
  return message.replace(/^JSON\.parse: /, '').replace(/^Unexpected/, 'Unexpected');
}

export function formatXmlParseError(doc: Document): string | null {
  const errorNode = doc.getElementsByTagName('parsererror')[0];
  if (!errorNode) return null;
  const text = errorNode.textContent?.trim() ?? 'Malformed XML.';
  return `Invalid XML: ${text.split('\n')[0]}`;
}
