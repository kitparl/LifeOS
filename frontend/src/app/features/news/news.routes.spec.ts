import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { environment } from '../../../environments/environment';
import { NAV_LUCIDE_ICON_PROVIDERS } from '../../shared/layout/nav-lucide';
import { NEWS_GUEST_PROVIDERS, NEWS_ROUTES } from './news.routes';

describe('NEWS_ROUTES', () => {
  const api = `${environment.apiUrl}/news`;
  const articleUrl = 'https://www.thehindu.com/a1';
  let http: HttpTestingController;
  let harness: RouterTestingHarness;

  beforeEach(async () => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        // Same two mounts as the app: authenticated `/news` and public `/explore/news`.
        provideRouter([
          { path: 'news', children: NEWS_ROUTES },
          { path: 'explore/news', providers: NEWS_GUEST_PROVIDERS, children: NEWS_ROUTES },
        ]),
        ...NAV_LUCIDE_ICON_PROVIDERS,
      ],
    });
    http = TestBed.inject(HttpTestingController);
    harness = await RouterTestingHarness.create();
  });

  const el = (): HTMLElement => harness.routeNativeElement as HTMLElement;
  const href = (testId: string): string | null | undefined =>
    el().querySelector(`[data-testid="${testId}"]`)?.getAttribute('href');

  it('article back link returns to the guest hub under /explore/news', async () => {
    await harness.navigateByUrl(`/explore/news/article?url=${encodeURIComponent(articleUrl)}`);
    expect(href('news-article-back-link')).toBe('/explore/news');
  });

  it('article back link returns to /news for signed-in users', async () => {
    await harness.navigateByUrl(`/news/article?url=${encodeURIComponent(articleUrl)}`);
    expect(href('news-article-back-link')).toBe('/news');
  });

  for (const tab of ['saved', 'collections']) {
    it(`guest ${tab} tab shows a locked panel with Sign in and loads no account data`, async () => {
      await harness.navigateByUrl(`/explore/news?tab=${tab}`);
      expect(el().textContent).toContain('Not available for free users');
      expect(href(`news-${tab}-locked-sign-in-link`)).toBe('/login');
      http.verify();
    });
  }

  it('signed-in saved tab still loads the library', async () => {
    await harness.navigateByUrl('/news?tab=saved');
    expect(el().querySelector('[data-testid="news-saved-locked"]')).toBeNull();
    http.expectOne((req) => req.url === `${api}/saved`);
  });

  it('redirects a guest collection deep link to the locked Collections tab', async () => {
    await harness.navigateByUrl('/explore/news/collections/c1');
    expect(TestBed.inject(Router).url).toBe('/explore/news?tab=collections');
    http.verify();
  });
});
