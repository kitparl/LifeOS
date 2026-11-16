import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { ImportJob } from '../models/activity.models';
import { ActivityService } from '../services/activity.service';
import { RunningSyncLogTabComponent } from './running-sync-log-tab.component';

const finished: ImportJob = {
  id: 'j1',
  status: 'finished',
  range_mode: '12m',
  files_found: 3,
  created: 2,
  duplicates: 0,
  outside_range: 0,
  not_activity: 0,
  failed: 1,
  runs_created: 2,
  runs_matched: 0,
  errors: [{ name: 'bad.fit', reason: 'File is damaged or incomplete' }],
  error: null,
  created_at: '2026-11-16T10:00:00Z',
  started_at: null,
  finished_at: null,
};

describe('RunningSyncLogTabComponent', () => {
  let activities: jasmine.SpyObj<ActivityService>;
  let confirm: jasmine.SpyObj<ConfirmService>;

  function create() {
    const fixture = TestBed.createComponent(RunningSyncLogTabComponent);
    fixture.detectChanges();
    return { fixture, cmp: fixture.componentInstance };
  }

  beforeEach(() => {
    activities = jasmine.createSpyObj<ActivityService>('ActivityService', [
      'listImports',
      'getImportedSummary',
      'deleteImportedData',
    ]);
    activities.listImports.and.returnValue(of({ items: [finished], total: 1 }));
    activities.getImportedSummary.and.returnValue(
      of({ activities: 2, runs_created: 1, runs_merged_into_manual: 1, health_days: 0 }),
    );
    confirm = jasmine.createSpyObj<ConfirmService>('ConfirmService', ['confirm']);
    TestBed.configureTestingModule({
      imports: [RunningSyncLogTabComponent],
      providers: [
        { provide: ActivityService, useValue: activities },
        { provide: ConfirmService, useValue: confirm },
      ],
    });
  });

  it('lists imports with their failed files', () => {
    const { fixture } = create();
    const text = fixture.nativeElement.textContent as string;

    expect(text).toContain('2 imported, 1 failed');
    expect(text).toContain('bad.fit — File is damaged or incomplete');
    expect(text).toContain('2 imported activities');
  });

  it('does nothing when the confirmation is cancelled', async () => {
    confirm.confirm.and.resolveTo(false);
    const { cmp } = create();

    await cmp.deleteImported();

    expect(activities.deleteImportedData).not.toHaveBeenCalled();
  });

  it('deletes imported data after confirmation, reports the result and asks the page to reload', async () => {
    confirm.confirm.and.resolveTo(true);
    activities.deleteImportedData.and.returnValue(
      of({ activities_deleted: 2, runs_deleted: 1, runs_restored: 1, races_detached: 0, files_deleted: 2, health_days_deleted: 0 }),
    );
    const { cmp } = create();
    const changed = jasmine.createSpy('changed');
    cmp.dataChanged.subscribe(changed);

    await cmp.deleteImported();

    expect(confirm.confirm.calls.mostRecent().args[0]).toContain('Runs you logged by hand keep your notes');
    expect(activities.deleteImportedData).toHaveBeenCalledOnceWith(false);
    expect(cmp.message()).toContain('Deleted 2 activities and 1 runs; 1 of your own runs restored');
    expect(changed).toHaveBeenCalledTimes(1);
    expect(activities.listImports).toHaveBeenCalledTimes(2); // reloaded
  });

  it('asks about Garmin health data only when there is some, and keeps it when that prompt is cancelled', async () => {
    activities.getImportedSummary.and.returnValue(
      of({ activities: 2, runs_created: 1, runs_merged_into_manual: 1, health_days: 12 }),
    );
    confirm.confirm.and.returnValues(Promise.resolve(true), Promise.resolve(false));
    activities.deleteImportedData.and.returnValue(
      of({ activities_deleted: 2, runs_deleted: 1, runs_restored: 1, races_detached: 0, files_deleted: 2, health_days_deleted: 0 }),
    );
    const { cmp } = create();

    await cmp.deleteImported();

    expect(confirm.confirm).toHaveBeenCalledTimes(2);
    expect(activities.deleteImportedData).toHaveBeenCalledOnceWith(false);
  });

  it('deletes Garmin health data too when the second prompt is accepted', async () => {
    activities.getImportedSummary.and.returnValue(
      of({ activities: 2, runs_created: 1, runs_merged_into_manual: 1, health_days: 12 }),
    );
    confirm.confirm.and.resolveTo(true);
    activities.deleteImportedData.and.returnValue(
      of({ activities_deleted: 2, runs_deleted: 1, runs_restored: 1, races_detached: 0, files_deleted: 2, health_days_deleted: 12 }),
    );
    const { cmp } = create();

    await cmp.deleteImported();

    expect(activities.deleteImportedData).toHaveBeenCalledOnceWith(true);
    expect(cmp.message()).toContain('12 days of Garmin health data deleted');
  });
});
