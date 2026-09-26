import { HttpHeaders, HttpResponse } from '@angular/common/http';
import { apiErrorMessage, toPage } from './http';

describe('http utils', () => {
  it('reads the total from X-Total-Count', () => {
    const res = new HttpResponse({ body: [1, 2], headers: new HttpHeaders({ 'X-Total-Count': '40' }) });
    expect(toPage(res)).toEqual({ items: [1, 2], total: 40 });
  });

  it('falls back to the body length and an empty list', () => {
    expect(toPage(new HttpResponse({ body: ['a'] }))).toEqual({ items: ['a'], total: 1 });
    expect(toPage(new HttpResponse<string[]>({ body: null }))).toEqual({ items: [], total: 0 });
  });

  it('extracts string, object, and validation-list details', () => {
    expect(apiErrorMessage({ error: { detail: 'Nope' } }, 'x')).toBe('Nope');
    expect(apiErrorMessage({ error: { detail: { code: 'c', message: 'Busy' } } }, 'x')).toBe('Busy');
    expect(apiErrorMessage({ error: { detail: [{ msg: 'Field required' }] } }, 'x')).toBe('Field required');
    expect(apiErrorMessage(null, 'fallback')).toBe('fallback');
  });
});
