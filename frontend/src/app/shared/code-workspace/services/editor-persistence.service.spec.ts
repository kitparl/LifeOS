import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { Subject } from 'rxjs';
import { EditorPersistenceService } from './editor-persistence.service';

describe('EditorPersistenceService', () => {
  let service: EditorPersistenceService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient()],
    });
    service = TestBed.inject(EditorPersistenceService);
  });

  afterEach(() => {
    service.disableAutosave('doc-1');
  });

  it('saves and loads drafts from IndexedDB', async () => {
    await service.saveDraft('doc-1', '# draft');
    const loaded = await service.loadDraft('doc-1');
    expect(loaded).toBe('# draft');
  });

  it('debounces autosave by 2.5s', fakeAsync(() => {
    const content$ = new Subject<string>();
    spyOn(service, 'saveDraft').and.resolveTo();
    service.enableAutosave('doc-1', content$);

    content$.next('a');
    tick(2499);
    expect(service.saveDraft).not.toHaveBeenCalled();
    tick(1);
    expect(service.saveDraft).toHaveBeenCalledWith('doc-1', 'a');
  }));
});
