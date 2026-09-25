import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { provideLucideIcons, LucideExternalLink, LucideFolderPlus, LucideNewspaper, LucideSearch, LucideStar } from '@lucide/angular';
import { environment } from '../../../../environments/environment';
import { SEARCH_DEBOUNCE_MS, NewsSearchTabComponent } from './search-tab.component';

describe('NewsSearchTabComponent', () => {
  let fixture: ComponentFixture<NewsSearchTabComponent>;
  let http: HttpTestingController;
  const url = `${environment.apiUrl}/news/articles`;
  const emptyPage = { items: [], total: 0, total_is_lower_bound: false, offset: 0, limit: 20, has_more: false };

  const type = (value: string) => {
    const input = fixture.nativeElement.querySelector('[data-testid="news-search-input"]') as HTMLInputElement;
    input.value = value;
    input.dispatchEvent(new Event('input'));
    settle();
  };

  /** Change detection plus effects (toObservable/toSignal run on effects). */
  const settle = () => {
    fixture.detectChanges();
    TestBed.flushEffects();
    fixture.detectChanges();
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NewsSearchTabComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        provideLucideIcons(LucideSearch, LucideStar, LucideFolderPlus, LucideExternalLink, LucideNewspaper),
      ],
    });
    http = TestBed.inject(HttpTestingController);
  });

  /** Created inside each fakeAsync test so the debounce timers run on the fake clock. */
  const create = () => {
    fixture = TestBed.createComponent(NewsSearchTabComponent);
    settle();
  };

  afterEach(() => http.verify());

  it('makes no request for an empty query', fakeAsync(() => {
    create();
    tick(SEARCH_DEBOUNCE_MS);
    fixture.detectChanges();
    http.expectNone((r) => r.url === url);
    expect(fixture.nativeElement.textContent).toContain('Search the latest news');
  }));

  it('debounces typing into a single request', fakeAsync(() => {
    create();
    type('a');
    tick(100);
    type('ai');
    tick(100);
    type('ai news');
    http.expectNone((r) => r.url === url);

    tick(SEARCH_DEBOUNCE_MS);
    settle(); // renders the feed with the debounced query and runs its query effect
    tick();
    const req = http.expectOne((r) => r.url === url);
    expect(req.request.params.get('q')).toBe('ai news');
    expect(req.request.params.get('lang')).toBe('en');
    req.flush(emptyPage);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No results');
  }));
});
