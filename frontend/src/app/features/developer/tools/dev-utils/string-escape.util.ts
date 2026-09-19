export function escapeStringLiteral(input: string): string {
  return JSON.stringify(input);
}

export function unescapeStringLiteral(input: string): string {
  const trimmed = input.trim();
  try {
    if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
      return JSON.parse(trimmed);
    }
    return JSON.parse('"' + trimmed.replace(/(?<!\\)"/g, '\\"') + '"');
  } catch {
    throw new Error('Could not unescape — check for invalid escape sequences.');
  }
}
