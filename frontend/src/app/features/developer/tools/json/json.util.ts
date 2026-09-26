import { formatJsonParseError } from '../../shared/dev-error.util';

export function parseJsonOrThrow(input: string): unknown {
  try {
    return JSON.parse(input);
  } catch (e) {
    throw new Error(formatJsonParseError(input, e));
  }
}
