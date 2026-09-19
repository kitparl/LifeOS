import { formatJsonParseError } from '../../shared/dev-error.util';

export function parseJsonOrThrow(input: string): unknown {
  try {
    return JSON.parse(input);
  } catch (e) {
    throw new Error(formatJsonParseError(input, e));
  }
}

export function prettyPrintJson(input: string, indent: number): string {
  return JSON.stringify(parseJsonOrThrow(input), null, indent);
}

export function minifyJson(input: string): string {
  return JSON.stringify(parseJsonOrThrow(input));
}
