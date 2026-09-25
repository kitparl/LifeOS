import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { NewsArticlePage } from '../models/news.models';
import { NEWS_CACHE_TTL_MS, NewsService } from './news.service';

describe('NewsService', () => {
  let service: NewsService;
  let http: HttpTestingController;
  let clock = 0;
  const api = `${environment.apiUrl}/news`;
  const page: NewsArticlePage = { items: [], total: 0, total_is_lower_bound: false, offset: 0, limit: 20, has_more: false };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(NewsService);
    http = TestBed.inject(HttpTestingController);
    clock = 1_000;
    service.now = () => clock;
  });

  afterEach(() => http.verify());

  it('sends only set query params and reuses the cached response within the TTL', () => {
    let calls = 0;
    service.articles({ category: 'ai', lang: 'en', q: '' }).subscribe(() => calls++);
    const req = http.expectOne((r) => r.url === `${api}/articles`);
    expect(req.request.params.keys().sort()).toEqual(['category', 'lang']);
    req.flush(page);

    clock += NEWS_CACHE_TTL_MS - 1;
    service.articles({ category: 'ai', lang: 'en' }).subscribe(() => calls++);
    http.expectNone(`${api}/articles`);
    expect(calls).toBe(2);
  });

  it('shares one in-flight request between concurrent subscribers', () => {
    const results: NewsArticlePage[] = [];
    service.articles({ q: 'climate' }).subscribe((p) => results.push(p));
    service.articles({ q: 'climate' }).subscribe((p) => results.push(p));
    http.expectOne((r) => r.url === `${api}/articles`).flush(page);
    expect(results.length).toBe(2);
  });

  it('refetches after the TTL', () => {
    service.categories().subscribe();
    http.expectOne(`${api}/categories`).flush([]);
    clock += NEWS_CACHE_TTL_MS;
    let refreshed = false;
    service.categories().subscribe(() => (refreshed = true));
    http.expectOne(`${api}/categories`).flush([]);
    expect(refreshed).toBeTrue();
  });

  it('does not cache errors', () => {
    service.article('https://example.com/a').subscribe({ error: () => undefined });
    http
      .expectOne((r) => r.url === `${api}/article`)
      .flush({ detail: { code: 'timeout' } }, { status: 503, statusText: 'Unavailable' });
    let recovered = false;
    service.article('https://example.com/a').subscribe(() => (recovered = true));
    http.expectOne((r) => r.url === `${api}/article`).flush({});
    expect(recovered).toBeTrue();
  });

  it('never caches writes', () => {
    service.save({
      article_external_id: 'a1',
      article_url: 'https://example.com/a',
      title: 'T',
      description: null,
      image: null,
      publisher: null,
      host: null,
      author: null,
      published_at: null,
    }).subscribe();
    const req = http.expectOne(`${api}/saved`);
    expect(req.request.method).toBe('POST');
    req.flush({});
    service.listSaved('all', 20, 0).subscribe();
    service.listSaved('all', 20, 0).subscribe();
    expect(http.match((r) => r.url === `${api}/saved`).length).toBe(2);
  });
});
