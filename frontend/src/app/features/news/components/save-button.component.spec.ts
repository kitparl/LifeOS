import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { provideLucideIcons, LucideFolderPlus, LucideStar } from '@lucide/angular';
import { environment } from '../../../../environments/environment';
import { NewsArticle } from '../models/news.models';
import { NEWS_ACCESS_MODE } from '../news-access-mode';
import { NewsSaveButtonComponent } from './save-button.component';

describe('NewsSaveButtonComponent', () => {
  let fixture: ComponentFixture<NewsSaveButtonComponent>;
  let http: HttpTestingController;
  const api = `${environment.apiUrl}/news`;
  const article: NewsArticle = {
    id: 'a1',
    url: 'https://www.thehindu.com/a1',
    title: 'Headline',
    description: null,
    published_at: null,
    host: 'www.thehindu.com',
    sitename: 'The Hindu',
    country: 'IN',
    lang: 'en',
    author: null,
    categories: null,
    image: null,
    saved_article_id: null,
  };
  const saved = {
    id: 's1',
    article_external_id: 'a1',
    article_url: article.url,
    title: 'Headline',
    description: null,
    image: null,
    publisher: 'The Hindu',
    host: 'www.thehindu.com',
    author: null,
    published_at: null,
    saved_at: '2026-09-25T10:00:00Z',
    expires_at: '2026-10-25T10:00:00Z',
    collection_ids: [] as string[],
    already_saved: false,
  };

  const button = (): HTMLButtonElement =>
    fixture.nativeElement.querySelector('[data-testid="news-save-button"]') as HTMLButtonElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [NewsSaveButtonComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideLucideIcons(LucideStar, LucideFolderPlus)],
    });
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(NewsSaveButtonComponent);
    fixture.componentRef.setInput('article', article);
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  it('has an accessible save label and saves a metadata snapshot', () => {
    expect(button().getAttribute('aria-label')).toBe('Save article');
    expect(button().getAttribute('aria-pressed')).toBe('false');

    button().click();
    const req = http.expectOne(`${api}/saved`);
    expect(req.request.body).toEqual(
      jasmine.objectContaining({ article_url: article.url, publisher: 'The Hindu', article_external_id: 'a1' }),
    );
    req.flush(saved);
    fixture.detectChanges();
    // The "Add to collection?" prompt loads collections right after saving.
    http.expectOne(`${api}/collections`).flush([]);
    fixture.detectChanges();

    expect(button().getAttribute('aria-label')).toBe('Remove saved article');
    expect(button().getAttribute('aria-pressed')).toBe('true');
    expect(fixture.nativeElement.textContent).toContain('Saved');
    expect(fixture.nativeElement.textContent).toContain('Add to collection?');
  });

  it('shows "Already saved" without prompting again', () => {
    button().click();
    http.expectOne(`${api}/saved`).flush({ ...saved, already_saved: true });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Already saved');
    expect(fixture.nativeElement.textContent).not.toContain('Add to collection?');
  });

  it('removes a saved article', () => {
    fixture.componentRef.setInput('article', { ...article, saved_article_id: 's1' });
    fixture.detectChanges();
    button().click();
    const req = http.expectOne(`${api}/saved/s1`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
    fixture.detectChanges();
    expect(button().getAttribute('aria-label')).toBe('Save article');
  });

  it('shows a friendly error message', () => {
    button().click();
    http
      .expectOne(`${api}/saved`)
      .flush({ detail: { code: 'write_limit', message: 'x' } }, { status: 429, statusText: 'Too Many Requests' });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('You have saved a lot this hour');
    expect(button().getAttribute('aria-label')).toBe('Save article');
  });

  describe('guest mode (Explore)', () => {
    let guestFixture: ComponentFixture<NewsSaveButtonComponent>;
    const el = (): HTMLElement => guestFixture.nativeElement as HTMLElement;
    const locked = (): HTMLButtonElement =>
      el().querySelector('[data-testid="news-save-button-locked"]') as HTMLButtonElement;

    beforeEach(() => {
      TestBed.resetTestingModule();
      TestBed.configureTestingModule({
        imports: [NewsSaveButtonComponent],
        providers: [
          provideHttpClient(),
          provideHttpClientTesting(),
          provideRouter([]),
          provideLucideIcons(LucideStar, LucideFolderPlus),
          { provide: NEWS_ACCESS_MODE, useValue: 'guest' },
        ],
      });
      http = TestBed.inject(HttpTestingController);
      guestFixture = TestBed.createComponent(NewsSaveButtonComponent);
      guestFixture.componentRef.setInput('article', article);
      guestFixture.detectChanges();
    });

    it('shows a locked star instead of the save button', () => {
      expect(el().querySelector('[data-testid="news-save-button"]')).toBeNull();
      expect(locked().getAttribute('aria-disabled')).toBe('true');
      expect(locked().getAttribute('aria-label')).toBe('Save article (sign in required)');
    });

    it('explains sign-in on click and never calls the save API', () => {
      locked().click();
      guestFixture.detectChanges();

      expect(locked().getAttribute('aria-expanded')).toBe('true');
      expect(el().textContent).toContain('Sign in to save articles');
      const signIn = el().querySelector('[data-testid="news-save-button-locked-sign-in-link"]');
      expect(signIn?.getAttribute('href')).toBe('/login');
      http.expectNone(() => true);
    });

    it('closes on Escape and on an outside click', () => {
      locked().click();
      guestFixture.detectChanges();
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
      guestFixture.detectChanges();
      expect(el().querySelector('[role="dialog"]')).toBeNull();

      locked().click();
      guestFixture.detectChanges();
      document.body.click();
      guestFixture.detectChanges();
      expect(el().querySelector('[role="dialog"]')).toBeNull();
    });
  });
});
