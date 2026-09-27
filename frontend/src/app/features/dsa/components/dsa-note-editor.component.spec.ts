import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SimpleChange } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { DsaNoteEditorComponent } from './dsa-note-editor.component';

const api = `${environment.apiUrl}/dsa`;

describe('DsaNoteEditorComponent', () => {
  let fixture: ComponentFixture<DsaNoteEditorComponent>;
  let component: DsaNoteEditorComponent;
  let http: HttpTestingController;

  function open(scope: 'patterns' | 'problems', slug: string, previous?: string): void {
    component.scope = scope;
    component.slug = slug;
    component.ngOnChanges({ slug: new SimpleChange(previous, slug, previous === undefined) });
  }

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(DsaNoteEditorComponent);
    component = fixture.componentInstance;
  });

  afterEach(() => http.verify());

  it('loads the note and only saves when the text changed', () => {
    open('problems', 'three-sum');
    http.expectOne(`${api}/problems/three-sum/note`).flush({ content: 'old', updated_at: '2026-09-27T10:00:00Z' });
    expect(component.loaded()).toBeTrue();
    expect(component.initialContent).toBe('old');

    component.persist(); // autosave with nothing new: no request
    http.expectNone(`${api}/problems/three-sum/note`);

    component.onContentChange('# two pointers after sorting');
    component.persist();
    const put = http.expectOne({ method: 'PUT', url: `${api}/problems/three-sum/note` });
    expect(put.request.body).toEqual({ content: '# two pointers after sorting' });
    expect(component.saveState()).toBe('saving');
    put.flush({ content: '# two pointers after sorting', updated_at: '2026-09-27T10:05:00Z' });
    expect(component.saveState()).toBe('saved');
    expect(component.savedAt()).toBe('2026-09-27T10:05:00Z');
  });

  it('saves unsaved text to the previous note when switching to another one', () => {
    open('problems', 'a');
    http.expectOne(`${api}/problems/a/note`).flush({ content: '', updated_at: null });
    component.onContentChange('note for a');

    open('problems', 'b', 'a');
    const put = http.expectOne({ method: 'PUT', url: `${api}/problems/a/note` });
    expect(put.request.body).toEqual({ content: 'note for a' });
    http.expectOne(`${api}/problems/b/note`).flush({ content: 'note for b', updated_at: null });

    put.flush({ content: 'note for a', updated_at: '2026-09-27T10:00:00Z' }); // late response for "a"
    expect(component.initialContent).toBe('note for b');
    expect(component.savedAt()).toBeNull(); // not overwritten by the stale save
    component.persist();
    http.expectNone({ method: 'PUT', url: `${api}/problems/b/note` }); // "b" is still unchanged
  });

  it('saves on destroy (leaving the tab or page)', () => {
    open('patterns', 'two-pointers');
    http.expectOne(`${api}/patterns/two-pointers/note`).flush({ content: '', updated_at: null });
    component.onContentChange('meet in the middle');
    fixture.destroy();
    http.expectOne({ method: 'PUT', url: `${api}/patterns/two-pointers/note` }).flush({ content: 'meet in the middle', updated_at: 'x' });
  });

  it('reports load and save failures', () => {
    open('patterns', 'two-pointers');
    http.expectOne(`${api}/patterns/two-pointers/note`).flush('boom', { status: 500, statusText: 'Server Error' });
    expect(component.loadError()).toBeTrue();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain("We couldn't load your note.");

    component.load();
    http.expectOne(`${api}/patterns/two-pointers/note`).flush({ content: '', updated_at: null });
    component.onContentChange('x');
    component.persist();
    http.expectOne({ method: 'PUT', url: `${api}/patterns/two-pointers/note` }).flush('no', { status: 500, statusText: 'Server Error' });
    expect(component.saveState()).toBe('error');
  });
});
