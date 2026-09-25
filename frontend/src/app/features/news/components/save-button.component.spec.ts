import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideLucideIcons, LucideFolderPlus, LucideStar } from '@lucide/angular';
import { environment } from '../../../../environments/environment';
import { NewsArticle } from '../models/news.models';
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
});
