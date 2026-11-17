import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { ImportJob } from '../../running/models/activity.models';
import { ActivityService } from '../../running/services/activity.service';
import { GarminConnectionStatus, IntegrationsService } from '../services/integrations.service';
import { GarminConfigComponent } from './garmin-config.component';

const disconnected: GarminConnectionStatus = {
  connected: false,
  key_masked: '',
  status: 'disconnected',
  last_sync_at: null,
  last_sync_message: null,
  last_sync_ok: null,
  synced_through: null,
};

const connected: GarminConnectionStatus = {
  ...disconnected,
  connected: true,
  key_masked: '****1234',
  status: 'synced',
  last_sync_message: 'Synced 2 new activities, 30 health days.',
  last_sync_ok: true,
};

const syncJob = (over: Partial<ImportJob> = {}): ImportJob => ({
  id: 's1',
  status: 'running',
  range_mode: '12m',
  origin: 'sync',
  health_days: 7,
  files_found: 1,
  created: 1,
  duplicates: 0,
  outside_range: 0,
  not_activity: 0,
  failed: 0,
  runs_created: 1,
  runs_matched: 0,
  errors: [],
  error: null,
  created_at: '2026-11-17T10:00:00Z',
  started_at: null,
  finished_at: null,
  ...over,
});

describe('GarminConfigComponent', () => {
  let integrations: jasmine.SpyObj<IntegrationsService>;
  let activities: jasmine.SpyObj<ActivityService>;
  let confirm: jasmine.SpyObj<ConfirmService>;

  function create() {
    const fixture = TestBed.createComponent(GarminConfigComponent);
    fixture.componentInstance.displayName = 'Garmin';
    fixture.componentInstance.description = 'Runs, activities and health data';
    fixture.detectChanges();
    return { fixture, cmp: fixture.componentInstance, text: () => fixture.nativeElement.textContent as string };
  }

  beforeEach(() => {
    integrations = jasmine.createSpyObj<IntegrationsService>('IntegrationsService', [
      'getGarmin',
      'saveGarminKey',
      'disconnectGarmin',
      'syncGarmin',
    ]);
    activities = jasmine.createSpyObj<ActivityService>('ActivityService', ['listImports', 'deleteImportedData']);
    confirm = jasmine.createSpyObj<ConfirmService>('ConfirmService', ['confirm']);
    integrations.getGarmin.and.returnValue(of(disconnected));
    activities.listImports.and.returnValue(of({ items: [], total: 0 }));
    TestBed.configureTestingModule({
      imports: [GarminConfigComponent],
      providers: [
        { provide: IntegrationsService, useValue: integrations },
        { provide: ActivityService, useValue: activities },
        { provide: ConfirmService, useValue: confirm },
      ],
    });
  });

  it('explains where the key comes from when not connected', () => {
    const { fixture, text } = create();
    const link = fixture.nativeElement.querySelector('a') as HTMLAnchorElement;

    expect(text()).toContain('Not connected');
    expect(link.href).toBe('https://connect.garmin.com/app/settings/personalApiToken');
    expect(fixture.nativeElement.querySelector('[data-testid="garmin-sync-button"]')).toBeNull();
  });

  it('saves a key, clears the field and starts following the first sync', () => {
    integrations.saveGarminKey.and.returnValue(of(connected));
    const { cmp, text, fixture } = create();
    cmp.keyInput = '  personal-key-1234  ';

    cmp.save();
    fixture.detectChanges();

    expect(integrations.saveGarminKey).toHaveBeenCalledWith('personal-key-1234', 1);
    expect(cmp.keyInput).toBe('');
    expect(text()).toContain('Key saved. The first sync has started.');
    expect(activities.listImports).toHaveBeenCalledTimes(2);
  });

  it('sends the chosen first-sync range with the key', () => {
    integrations.saveGarminKey.and.returnValue(of(connected));
    const { cmp } = create();
    cmp.keyInput = 'personal-key-1234';
    cmp.firstSyncMonths = 6;

    cmp.save();

    expect(integrations.saveGarminKey).toHaveBeenCalledWith('personal-key-1234', 6);
  });

  it('syncs since the last sync by default, or the chosen months', () => {
    integrations.getGarmin.and.returnValue(of({ ...connected, synced_through: '2026-11-16' }));
    integrations.syncGarmin.and.returnValue(of(syncJob({ status: 'finished' })));
    const { cmp, fixture } = create();
    const options = Array.from(
      (fixture.nativeElement.querySelector('[data-testid="garmin-sync-range"]') as HTMLSelectElement).options,
    ).map((o) => o.textContent?.trim());

    cmp.syncNow();
    cmp.syncMonths = 3;
    cmp.syncNow();

    expect(options).toEqual(['Since last sync', 'Last 1 month', 'Last 3 months', 'Last 6 months', 'Last 9 months', 'Last 12 months']);
    expect(integrations.syncGarmin.calls.allArgs()).toEqual([[null], [3]]);
  });

  it('offers "Since last sync" only after a sync has stored data', () => {
    integrations.getGarmin.and.returnValue(of(connected));
    const { cmp, fixture } = create();
    const select = fixture.nativeElement.querySelector('[data-testid="garmin-sync-range"]') as HTMLSelectElement;

    expect(Array.from(select.options).map((o) => o.textContent?.trim())).not.toContain('Since last sync');
    expect(cmp.syncMonths).toBe(1);
  });

  it('shows why a key was refused', () => {
    integrations.saveGarminKey.and.returnValue(
      throwError(() => new HttpErrorResponse({ status: 400, error: { detail: 'Garmin did not accept this key.' } })),
    );
    const { cmp, text, fixture } = create();
    cmp.keyInput = 'bad-key';

    cmp.save();
    fixture.detectChanges();

    expect(text()).toContain('Garmin did not accept this key.');
    expect(cmp.busy()).toBeFalse();
  });

  it('shows progress while a sync runs and hides the previous result', () => {
    integrations.getGarmin.and.returnValue(
      of({ ...connected, last_sync_message: 'Could not reach Garmin.', last_sync_ok: false, synced_through: '2026-03-01' }),
    );
    activities.listImports.and.returnValue(of({ items: [syncJob()], total: 1 }));
    const { cmp, text, fixture } = create();
    fixture.detectChanges();

    expect(cmp.syncing()).toBeTrue();
    expect(text()).toContain('Syncing…');
    expect(text()).toContain('1 imported, 7 health days');
    expect(text()).toContain('checked up to Mar 1, 2026');
    expect(text()).not.toContain('Could not reach Garmin.');
    cmp.ngOnDestroy();
  });

  it('removes the key and keeps the data when the second question is declined', async () => {
    integrations.getGarmin.and.returnValue(of(connected));
    integrations.disconnectGarmin.and.returnValue(of(undefined));
    confirm.confirm.and.returnValues(Promise.resolve(true), Promise.resolve(false));
    const { cmp } = create();

    await cmp.remove();

    expect(integrations.disconnectGarmin).toHaveBeenCalled();
    expect(activities.deleteImportedData).not.toHaveBeenCalled();
    expect(cmp.message()).toBe('Garmin key removed. Your imported data is kept.');
  });

  it('removes the key and the imported data when both questions are accepted', async () => {
    integrations.getGarmin.and.returnValue(of(connected));
    integrations.disconnectGarmin.and.returnValue(of(undefined));
    activities.deleteImportedData.and.returnValue(
      of({ activities_deleted: 1, runs_deleted: 1, runs_restored: 0, races_detached: 0, files_deleted: 1, health_days_deleted: 3 }),
    );
    confirm.confirm.and.returnValues(Promise.resolve(true), Promise.resolve(true));
    const { cmp } = create();

    await cmp.remove();

    expect(activities.deleteImportedData).toHaveBeenCalledWith(true);
    expect(cmp.message()).toBe('Garmin key removed and imported data deleted.');
  });
});
