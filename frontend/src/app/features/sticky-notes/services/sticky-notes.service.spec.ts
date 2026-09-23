import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { StickyNotesService } from './sticky-notes.service';

describe('StickyNotesService', () => {
  let service: StickyNotesService;
  let http: HttpTestingController;

  const sampleNote = {
    id: '1',
    title: null,
    content: 'Buy milk',
    color: 'yellow',
    is_pinned: false,
    order_index: 0,
    note_month: '2026-09',
    tags: [] as string[],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    deleted_at: null,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(StickyNotesService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('creates a note', () => {
    service.create({ content: 'Buy milk' }).subscribe((n) => {
      expect(n.content).toBe('Buy milk');
    });
    const req = http.expectOne(`${environment.apiUrl}/sticky-notes`);
    expect(req.request.method).toBe('POST');
    req.flush(sampleNote);
  });

  it('lists notes by month', () => {
    service.listByMonth('2026-09').subscribe((notes) => {
      expect(notes.length).toBe(1);
    });
    const req = http.expectOne((r) => r.url === `${environment.apiUrl}/sticky-notes` && r.params.get('month') === '2026-09');
    expect(req.request.method).toBe('GET');
    req.flush([sampleNote]);
  });

  it('lists months with counts', () => {
    service.listMonths().subscribe((months) => {
      expect(months).toEqual([{ month: '2026-09', note_count: 1 }]);
    });
    const req = http.expectOne(`${environment.apiUrl}/sticky-notes/months`);
    expect(req.request.method).toBe('GET');
    req.flush([{ month: '2026-09', note_count: 1 }]);
  });

  it('searches notes', () => {
    service.search('milk').subscribe((notes) => {
      expect(notes[0].content).toBe('Buy milk');
    });
    const req = http.expectOne((r) => r.url === `${environment.apiUrl}/sticky-notes/search` && r.params.get('q') === 'milk');
    req.flush([sampleNote]);
  });

  it('updates a note (e.g. reorder/pin/color)', () => {
    service.update('1', { is_pinned: true }).subscribe((n) => {
      expect(n.is_pinned).toBe(true);
    });
    const req = http.expectOne(`${environment.apiUrl}/sticky-notes/1`);
    expect(req.request.method).toBe('PATCH');
    req.flush({ ...sampleNote, is_pinned: true });
  });

  it('deletes a note', () => {
    service.delete('1').subscribe();
    const req = http.expectOne(`${environment.apiUrl}/sticky-notes/1`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('restores a soft-deleted note', () => {
    service.restore('1').subscribe((n) => {
      expect(n.deleted_at).toBeNull();
    });
    const req = http.expectOne(`${environment.apiUrl}/sticky-notes/1/restore`);
    expect(req.request.method).toBe('POST');
    req.flush(sampleNote);
  });

  it('lists all notes across months', () => {
    service.listAll().subscribe((notes) => {
      expect(notes.length).toBe(1);
    });
    const req = http.expectOne(`${environment.apiUrl}/sticky-notes/all`);
    expect(req.request.method).toBe('GET');
    req.flush([sampleNote]);
  });

  it('creates a note with tags', () => {
    service.create({ content: 'Standup notes', tags: ['scrum', 'meeting'] }).subscribe((n) => {
      expect(n.tags).toEqual(['scrum', 'meeting']);
    });
    const req = http.expectOne(`${environment.apiUrl}/sticky-notes`);
    expect(req.request.body.tags).toEqual(['scrum', 'meeting']);
    req.flush({ ...sampleNote, tags: ['scrum', 'meeting'] });
  });

  it('updates tags on an existing note', () => {
    service.update('1', { tags: ['scrum'] }).subscribe((n) => {
      expect(n.tags).toEqual(['scrum']);
    });
    const req = http.expectOne(`${environment.apiUrl}/sticky-notes/1`);
    expect(req.request.body.tags).toEqual(['scrum']);
    req.flush({ ...sampleNote, tags: ['scrum'] });
  });

  it('lists soft-deleted notes', () => {
    service.listDeleted().subscribe((notes) => {
      expect(notes.length).toBe(1);
    });
    const req = http.expectOne(`${environment.apiUrl}/sticky-notes/deleted`);
    expect(req.request.method).toBe('GET');
    req.flush([{ ...sampleNote, deleted_at: new Date().toISOString() }]);
  });
});
