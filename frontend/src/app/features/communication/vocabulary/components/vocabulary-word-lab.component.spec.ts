import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { environment } from '../../../../../environments/environment';
import { VocabularyWordLabComponent } from './vocabulary-word-lab.component';

const API = `${environment.apiUrl}/communication/vocabulary/word-lab`;

describe('VocabularyWordLabComponent', () => {
  let fixture: ComponentFixture<VocabularyWordLabComponent>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VocabularyWordLabComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
    fixture = TestBed.createComponent(VocabularyWordLabComponent);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function text(): string {
    return fixture.nativeElement.textContent as string;
  }

  function connect(usage: number | null = 73): void {
    fixture.detectChanges();
    http.expectOne(`${API}/status`).flush({ connected: true, usage_remaining_pct: usage });
    fixture.detectChanges();
  }

  it('shows the Integrations call to action and makes no lookups when not connected', () => {
    fixture.detectChanges();
    http.expectOne(`${API}/status`).flush({ connected: false, usage_remaining_pct: null });
    fixture.detectChanges();

    const link: HTMLAnchorElement = fixture.nativeElement.querySelector('[data-testid="word-lab-locked"] a');
    expect(link.textContent).toContain('Connect in Integrations');
    expect(link.getAttribute('href')).toBe('/integrations#wordnik');
    expect(fixture.nativeElement.querySelector('input')).toBeNull();
    http.expectNone((r) => r.url.startsWith(`${API}/lookup`));
  });

  it('shows usage and "Unknown" when the percentage is not known', () => {
    connect(null);
    expect(text()).toContain('Usage remaining: Unknown');
  });

  it('looks up in the selected mode and re-runs the query when the mode changes', () => {
    connect();
    fixture.componentInstance.query.set('herald');
    fixture.componentInstance.search();
    http.expectOne(`${API}/lookup?q=herald&mode=dictionary`).flush({
      mode: 'dictionary',
      query: 'herald',
      definitions: [{ part_of_speech: 'noun', text: 'A messenger.' }],
      example: 'The herald spoke.',
      words: [],
      usage_remaining_pct: 72,
    });
    fixture.detectChanges();
    expect(text()).toContain('A messenger.');
    expect(text()).toContain('Save as vocabulary');
    expect(text()).toContain('Usage remaining: 72%');

    fixture.componentInstance.selectTool('synonyms');
    http.expectOne(`${API}/lookup?q=herald&mode=synonyms`).flush({
      mode: 'synonyms',
      query: 'herald',
      definitions: [],
      example: null,
      words: [{ word: 'envoy', hint: null }],
      usage_remaining_pct: 71,
    });
    fixture.detectChanges();
    expect(text()).toContain('envoy');
  });

  it('switches to the locked state when the key turns out to be missing', () => {
    connect();
    fixture.componentInstance.query.set('herald');
    fixture.componentInstance.search();
    http
      .expectOne(`${API}/lookup?q=herald&mode=dictionary`)
      .flush({ detail: { code: 'missing_credential', message: 'x' } }, { status: 400, statusText: 'Bad Request' });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="word-lab-locked"]')).not.toBeNull();
  });
});
