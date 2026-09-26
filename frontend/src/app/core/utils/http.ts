import { HttpResponse } from '@angular/common/http';

/** One page of a list endpoint; `total` comes from the `X-Total-Count` header. */
export interface Page<T> {
  items: T[];
  total: number;
}

/** Map an `observe: 'response'` list call to a {@link Page}. */
export function toPage<T>(response: HttpResponse<T[]>): Page<T> {
  return {
    items: response.body ?? [],
    total: Number(response.headers.get('X-Total-Count') ?? response.body?.length ?? 0),
  };
}

/** API errors carry `detail` as a string, `{code, message}`, or a 422 validation list. */
export function apiErrorMessage(err: unknown, fallback: string): string {
  const detail = (err as { error?: { detail?: unknown } } | null)?.error?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const first = detail[0] as { msg?: string } | undefined;
    return first?.msg ?? fallback;
  }
  const message = (detail as { message?: string } | undefined)?.message;
  return message ?? fallback;
}
