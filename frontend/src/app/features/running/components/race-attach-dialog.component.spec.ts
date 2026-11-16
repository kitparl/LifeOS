import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { RaceEvent, RunListItem } from '../models/running.models';
import { RunningService } from '../services/running.service';
import { RaceAttachDialogComponent } from './race-attach-dialog.component';

const run = (id: string): RunListItem => ({
  id,
  run_date: '2026-05-03',
  distance_km: 10.2,
  duration_seconds: 3121,
  pace_min_per_km: 5.1,
  weather: null,
  location: null,
  shoe: null,
  updated_at: '2026-05-03T10:00:00Z',
});

describe('RaceAttachDialogComponent', () => {
  let running: jasmine.SpyObj<RunningService>;

  function create(raceId = 'race1') {
    const fixture = TestBed.createComponent(RaceAttachDialogComponent);
    fixture.componentRef.setInput('raceId', raceId);
    fixture.componentRef.setInput('open', true);
    fixture.detectChanges();
    return { fixture, cmp: fixture.componentInstance };
  }

  beforeEach(() => {
    running = jasmine.createSpyObj<RunningService>('RunningService', ['listRaceCandidates', 'attachRun']);
    TestBed.configureTestingModule({
      imports: [RaceAttachDialogComponent],
      providers: [{ provide: RunningService, useValue: running }],
    });
  });

  it('loads the candidates when it opens and renders them in the order the server gave', () => {
    running.listRaceCandidates.and.returnValue(of([run('a'), run('b')]));

    const { fixture } = create();

    expect(running.listRaceCandidates).toHaveBeenCalledOnceWith('race1');
    const buttons = fixture.nativeElement.querySelectorAll('[data-testid^="race-attach-choose-"]');
    expect(Array.from(buttons).map((b) => (b as HTMLElement).dataset['testid'])).toEqual([
      'race-attach-choose-a',
      'race-attach-choose-b',
    ]);
  });

  it('explains when there is nothing to attach', () => {
    running.listRaceCandidates.and.returnValue(of([]));

    const { fixture } = create();

    expect(fixture.nativeElement.querySelector('[data-testid="race-attach-empty"]').textContent).toContain(
      'No synced runs within 3 days of this race.',
    );
  });

  it('attaches the chosen run and reports the updated race', () => {
    running.listRaceCandidates.and.returnValue(of([run('a')]));
    const race = { id: 'race1', run_id: 'a' } as RaceEvent;
    running.attachRun.and.returnValue(of(race));
    const { cmp } = create();
    const attached = jasmine.createSpy('attached');
    cmp.attached.subscribe(attached);

    cmp.attach(run('a'));

    expect(running.attachRun).toHaveBeenCalledOnceWith('race1', 'a');
    expect(attached).toHaveBeenCalledOnceWith(race);
  });

  it('shows the server message when attaching fails, for example when the run is already attached', () => {
    running.listRaceCandidates.and.returnValue(of([run('a')]));
    running.attachRun.and.returnValue(
      throwError(() => ({ error: { detail: 'This run is already attached to another race' } })),
    );
    const { cmp } = create();

    cmp.attach(run('a'));

    expect(cmp.error()).toBe('This run is already attached to another race');
    expect(cmp.busy()).toBeFalse();
  });
});
