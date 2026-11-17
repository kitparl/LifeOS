import { HttpErrorResponse } from '@angular/common/http';
import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { ImportJob } from '../../running/models/activity.models';
import { ActivityService } from '../../running/services/activity.service';
import { GarminConnectionStatus, GarminSyncScope, IntegrationsService } from '../services/integrations.service';
import { GarminSyncComponent } from './garmin-sync.component';

const connected: GarminConnectionStatus = {
  connected: true,
  key_masked: '****1234',
  status: 'synced',
  last_sync_at: null,
  last_sync_message: 'Synced 3 health days.',
  last_sync_ok: true,
  synced_through: '2026-11-16',
  activities_synced_through: null,
};

const job = (over: Partial<ImportJob> = {}): ImportJob => ({
  id: 's1',
  status: 'running',
  range_mode: 'recent',
  origin: 'sync',
  health_days: 3,
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
  created_at: '2026-11-17T10:00:00Z',
  started_at: null,
  finished_at: null,
  ...over,
});

describe('GarminSyncComponent', () => {
  let integrations: jasmine.SpyObj<IntegrationsService>;
  let activities: jasmine.SpyObj<ActivityService>;

  function create(scope: GarminSyncScope = 'health') {
    const fixture = TestBed.createComponent(GarminSyncComponent);
    fixture.componentInstance.scope = scope;
    fixture.detectChanges();
    const options = () =>
      Array.from((fixture.nativeElement.querySelector('[data-testid="garmin-sync-range"]') as HTMLSelectElement).options).map(
        (o) => o.textContent?.trim(),
      );
    return { fixture, cmp: fixture.componentInstance, text: () => fixture.nativeElement.textContent as string, options };
  }

  beforeEach(() => {
    integrations = jasmine.createSpyObj<IntegrationsService>('IntegrationsService', ['getGarmin', 'syncGarmin']);
    activities = jasmine.createSpyObj<ActivityService>('ActivityService', ['listImports']);
    integrations.getGarmin.and.returnValue(of(connected));
    activities.listImports.and.returnValue(of({ items: [], total: 0 }));
    TestBed.configureTestingModule({
      imports: [GarminSyncComponent],
      providers: [
        { provide: IntegrationsService, useValue: integrations },
        { provide: ActivityService, useValue: activities },
      ],
    });
  });

  it('shows nothing until Garmin is connected', () => {
    integrations.getGarmin.and.returnValue(of({ ...connected, connected: false }));
    const { fixture } = create();

    expect(fixture.nativeElement.querySelector('[data-testid="garmin-sync-button"]')).toBeNull();
  });

  it('syncs only its own part, since the last sync by default or over the chosen months', () => {
    integrations.syncGarmin.and.returnValue(of(job()));
    const { cmp, options, text } = create('health');

    cmp.syncNow();
    cmp.months = 6;
    cmp.syncNow();

    expect(options()).toEqual(['Since last sync', 'Last 1 month', 'Last 3 months', 'Last 6 months', 'Last 9 months', 'Last 12 months']);
    expect(text()).toContain('Sync Garmin');
    expect(integrations.syncGarmin.calls.allArgs()).toEqual([[null, 'health'], [6, 'health']]);
    cmp.ngOnDestroy();
  });

  it('offers "Since last sync" only once its own part has synced', () => {
    const { cmp, options } = create('activities'); // health has a cursor, activities do not

    expect(options()).not.toContain('Since last sync');
    expect(cmp.months).toBe(1);
  });

  it('follows a running sync, then shows the result and reports that it finished', fakeAsync(() => {
    activities.listImports.and.returnValues(
      of({ items: [job()], total: 1 }),
      of({ items: [job({ status: 'finished' })], total: 1 }),
    );
    const { cmp, fixture, text } = create('health');
    const finished = jasmine.createSpy('finished');
    cmp.finished.subscribe(finished);
    fixture.detectChanges();

    expect(text()).toContain('Syncing…');
    expect(text()).toContain('3 health days');

    tick(3000);
    fixture.detectChanges();

    expect(cmp.syncing()).toBeFalse();
    expect(finished).toHaveBeenCalledTimes(1);
    expect(text()).toContain('Synced 3 health days.');
  }));

  it('explains why a sync could not start', () => {
    integrations.syncGarmin.and.returnValue(
      throwError(() => new HttpErrorResponse({ status: 409, error: { detail: 'An import is already running' } })),
    );
    const { cmp, fixture, text } = create();

    cmp.syncNow();
    fixture.detectChanges();

    expect(text()).toContain('An import is already running');
  });
});
