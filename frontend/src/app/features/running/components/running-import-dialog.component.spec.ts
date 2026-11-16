import { fakeAsync, tick, discardPeriodicTasks } from '@angular/core/testing';
import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { ImportJob } from '../models/activity.models';
import { ActivityService } from '../services/activity.service';
import { RunningImportDialogComponent } from './running-import-dialog.component';

const job = (status: ImportJob['status'], over: Partial<ImportJob> = {}): ImportJob => ({
  id: 'j1',
  status,
  range_mode: '12m',
  files_found: 0,
  created: 0,
  duplicates: 0,
  outside_range: 0,
  not_activity: 0,
  failed: 0,
  runs_created: 0,
  runs_matched: 0,
  errors: [],
  error: null,
  created_at: '2026-11-16T10:00:00Z',
  started_at: null,
  finished_at: null,
  ...over,
});

describe('RunningImportDialogComponent', () => {
  let activities: jasmine.SpyObj<ActivityService>;

  function create() {
    const fixture = TestBed.createComponent(RunningImportDialogComponent);
    const cmp = fixture.componentInstance;
    cmp.open = true;
    fixture.componentRef.setInput('open', true);
    fixture.detectChanges();
    return { fixture, cmp };
  }

  beforeEach(() => {
    activities = jasmine.createSpyObj<ActivityService>('ActivityService', ['startImport', 'getImport']);
    TestBed.configureTestingModule({
      imports: [RunningImportDialogComponent],
      providers: [{ provide: ActivityService, useValue: activities }],
    });
  });

  it('cannot start without files', () => {
    const { cmp } = create();
    cmp.start();
    expect(activities.startImport).not.toHaveBeenCalled();
  });

  it('starts an import, polls until it finishes, then reports it once', fakeAsync(() => {
    const { cmp } = create();
    const imported = jasmine.createSpy('imported');
    cmp.imported.subscribe(imported);
    activities.startImport.and.returnValue(of(job('queued')));
    const polls = [job('running', { files_found: 1 }), job('finished', { files_found: 2, created: 2, runs_created: 2 })];
    activities.getImport.and.callFake(() => of(polls.shift()!));
    cmp.files.set([new File(['x'], 'a.fit')]);
    cmp.range.set('all');

    cmp.start();
    expect(activities.startImport).toHaveBeenCalledWith(jasmine.any(Array), 'all');
    expect(cmp.job()?.status).toBe('queued');

    tick(1500);
    expect(cmp.job()?.status).toBe('running');
    expect(imported).not.toHaveBeenCalled();

    tick(1500);
    expect(cmp.job()?.status).toBe('finished');
    expect(imported).toHaveBeenCalledTimes(1);

    tick(10_000);
    expect(activities.getImport).toHaveBeenCalledTimes(2); // polling stopped
    discardPeriodicTasks();
  }));

  it('shows the server message when the upload is rejected and lets the user try again', () => {
    const { cmp } = create();
    activities.startImport.and.returnValue(
      throwError(() => ({ error: { detail: 'Unsupported file type; upload .fit files or a Garmin export .zip' } })),
    );
    cmp.files.set([new File(['x'], 'notes.fit')]);

    cmp.start();

    expect(cmp.error()).toContain('Unsupported file type');
    expect(cmp.busy()).toBeFalse();
    expect(cmp.job()).toBeNull();
  });

  it('stops polling when the dialog is closed while the import keeps running', fakeAsync(() => {
    const { cmp } = create();
    const closed = jasmine.createSpy('closed');
    cmp.closed.subscribe(closed);
    activities.startImport.and.returnValue(of(job('running')));
    activities.getImport.and.returnValue(of(job('running')));
    cmp.files.set([new File(['x'], 'a.fit')]);

    cmp.start();
    tick(1500);
    expect(activities.getImport).toHaveBeenCalledTimes(1);

    cmp.close();
    tick(5000);

    expect(closed).toHaveBeenCalled();
    expect(activities.getImport).toHaveBeenCalledTimes(1);
    discardPeriodicTasks();
  }));

  it('resets when it is opened again', () => {
    const { fixture, cmp } = create();
    cmp.files.set([new File(['x'], 'a.fit')]);
    cmp.error.set('old error');

    fixture.componentRef.setInput('open', false);
    fixture.detectChanges();
    fixture.componentRef.setInput('open', true);
    fixture.detectChanges();

    expect(cmp.files()).toEqual([]);
    expect(cmp.error()).toBe('');
  });
});
