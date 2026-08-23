import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { EditorPreferencesService } from './editor-preferences.service';
import { environment } from '../../../environments/environment';

describe('EditorPreferencesService', () => {
  let service: EditorPreferencesService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(EditorPreferencesService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('defaults to default keymap', () => {
    expect(service.keymap()).toBe('default');
  });

  it('loads keymap from API on init', () => {
    service.init();

    const req = httpMock.expectOne(`${environment.apiUrl}/preferences/editor`);
    expect(req.request.method).toBe('GET');
    req.flush({ key: 'editor', value: { keymap: 'vim' } });

    expect(service.keymap()).toBe('vim');
  });

  it('falls back to default for invalid API values', () => {
    service.init();

    const req = httpMock.expectOne(`${environment.apiUrl}/preferences/editor`);
    req.flush({ key: 'editor', value: { keymap: 'emacs' } });

    expect(service.keymap()).toBe('default');
  });

  it('seeds from localStorage before API responds', () => {
    localStorage.setItem('lifeos-editor-prefs', JSON.stringify({ keymap: 'vim' }));

    service.init();
    expect(service.keymap()).toBe('vim');

    const req = httpMock.expectOne(`${environment.apiUrl}/preferences/editor`);
    req.flush({ key: 'editor', value: null });
  });

  it('saves keymap and updates signal', () => {
    service.setKeymap('vim');
    expect(service.keymap()).toBe('vim');

    const req = httpMock.expectOne(`${environment.apiUrl}/preferences/editor`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual({ value: { keymap: 'vim' } });
    req.flush({ key: 'editor', value: { keymap: 'vim' } });

    const cached = JSON.parse(localStorage.getItem('lifeos-editor-prefs') || '{}');
    expect(cached.keymap).toBe('vim');
  });
});
