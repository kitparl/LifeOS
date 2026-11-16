import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { HealthDay, MetricInfo } from '../models/health.models';
import { HealthService } from '../services/health.service';
import { HealthDayFormComponent } from './health-day-form.component';

const catalogue: MetricInfo[] = [
  { key: 'resting_hr', label: 'Resting heart rate', unit: 'bpm', group: 'heart', kind: 'int', min: 20, max: 150, lower_is_better: true, today: true },
  { key: 'steps', label: 'Steps', unit: '', group: 'activity', kind: 'int', min: 0, max: 200000, lower_is_better: false, today: false },
  { key: 'bed_time_min', label: 'Bed time', unit: '', group: 'sleep', kind: 'clock', min: 0, max: 1439, lower_is_better: null, today: false },
];

describe('HealthDayFormComponent', () => {
  let health: jasmine.SpyObj<HealthService>;

  function create() {
    const fixture = TestBed.createComponent(HealthDayFormComponent);
    fixture.componentRef.setInput('catalogue', catalogue);
    fixture.componentRef.setInput('open', true);
    fixture.detectChanges();
    return { fixture, cmp: fixture.componentInstance };
  }

  beforeEach(() => {
    health = jasmine.createSpyObj<HealthService>('HealthService', ['getDay', 'saveDay']);
    health.getDay.and.returnValue(throwError(() => ({ status: 404 })));
    TestBed.configureTestingModule({
      imports: [HealthDayFormComponent],
      providers: [{ provide: HealthService, useValue: health }],
    });
  });

  const fill = (cmp: HealthDayFormComponent, key: string, value: string) =>
    cmp.setText(key, { target: { value } } as unknown as Event);

  it('refuses to save without any value', () => {
    const { cmp } = create();
    cmp.save();
    expect(health.saveDay).not.toHaveBeenCalled();
    expect(cmp.error()).toBe('Enter at least one value.');
  });

  it('saves only the filled fields, converting the clock time to minutes', () => {
    health.saveDay.and.returnValue(of({ day: 'x', values: {}, sources: {} } as HealthDay));
    const { cmp } = create();
    const saved = jasmine.createSpy('saved');
    cmp.saved.subscribe(saved);
    fill(cmp, 'resting_hr', '52');
    fill(cmp, 'bed_time_min', '23:30');
    fill(cmp, 'steps', '');

    cmp.save();

    expect(health.saveDay).toHaveBeenCalledOnceWith(cmp.date(), { resting_hr: 52, bed_time_min: 1410 });
    expect(saved).toHaveBeenCalledTimes(1);
  });

  it('names the fields that are not valid before calling the server', () => {
    const { cmp } = create();
    fill(cmp, 'resting_hr', 'fast');

    cmp.save();

    expect(health.saveDay).not.toHaveBeenCalled();
    expect(cmp.error()).toContain('Resting heart rate');
  });

  it('shows the server message without its technical prefix', () => {
    health.saveDay.and.returnValue(
      throwError(() => ({ error: { detail: [{ msg: 'Value error, Resting heart rate must be between 20 and 150' }] } })),
    );
    const { cmp } = create();
    fill(cmp, 'resting_hr', '400');

    cmp.save();

    expect(cmp.error()).toBe('Resting heart rate must be between 20 and 150');
    expect(cmp.busy()).toBeFalse();
  });

  it('prefills the values you entered and shows imported values only as hints', () => {
    health.getDay.and.returnValue(
      of({ day: 'x', values: { resting_hr: 50, steps: 9000 }, sources: { resting_hr: 'manual', steps: 'garmin' } }),
    );

    const { cmp } = create();

    expect(cmp.texts()).toEqual({ resting_hr: '50' });
    expect(cmp.hints()).toEqual({ steps: 9000 });
  });
});
