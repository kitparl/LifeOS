import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { environment } from '../../../../../environments/environment';
import { NAV_LUCIDE_ICON_PROVIDERS } from '../../../../shared/layout/nav-lucide';
import { VocabularyBookmarksComponent } from './vocabulary-bookmarks.component';

describe('VocabularyBookmarksComponent', () => {
  let fixture: ComponentFixture<VocabularyBookmarksComponent>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VocabularyBookmarksComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        ...NAV_LUCIDE_ICON_PROVIDERS,
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(VocabularyBookmarksComponent);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should list bookmarked words in one place', () => {
    fixture.detectChanges();
    const req = http.expectOne(`${environment.apiUrl}/communication/vocabulary/bookmarks?limit=20&offset=0`);
    req.flush({
      total: 1,
      items: [
        {
          id: 'b1',
          created_at: '2026-09-19T00:00:00Z',
          vocabulary: {
            id: 'v000001',
            term: 'hello',
            type: 'WORD',
            level: 'A1',
            part_of_speech: 'interjection',
            simple_meaning: 'a greeting',
            example: 'Hello there.',
            pronunciation: null,
          },
        },
      ],
    });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('hello');
    expect(fixture.nativeElement.textContent).toContain('a greeting');
  });

  it('should remove a bookmark from the list', () => {
    fixture.detectChanges();
    http.expectOne((r) => r.url.startsWith(`${environment.apiUrl}/communication/vocabulary/bookmarks`)).flush({
      total: 1,
      items: [
        {
          id: 'b1',
          created_at: '2026-09-19T00:00:00Z',
          vocabulary: {
            id: 'v000001',
            term: 'hello',
            type: 'WORD',
            level: 'A1',
            part_of_speech: 'interjection',
            simple_meaning: 'a greeting',
            example: 'Hello there.',
            pronunciation: null,
          },
        },
      ],
    });
    fixture.detectChanges();
    fixture.componentInstance.remove(fixture.componentInstance.items()[0]);
    const del = http.expectOne(`${environment.apiUrl}/communication/vocabulary/bookmarks/v000001`);
    expect(del.request.method).toBe('DELETE');
    del.flush(null);
    http.expectOne((r) => r.url.startsWith(`${environment.apiUrl}/communication/vocabulary/bookmarks`)).flush({
      total: 0,
      items: [],
    });
    expect(fixture.componentInstance.items().length).toBe(0);
  });
});
