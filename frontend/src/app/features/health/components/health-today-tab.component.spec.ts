import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { HealthToday } from '../models/health.models';
import { HealthService } from '../services/health.service';
import { HealthTodayTabComponent } from './health-today-tab.component';

const metric = (over: Record<string, unknown>) => ({
  key: 'resting_hr',
  label: 'Resting heart rate',
  unit: 'bpm',
  value: 58,
  avg_7d: 53,
  avg_30d: 52,
  marker: 'up',
  favourable: 'bad',
  needs_more_data: false,
  ...over,
});

describe('HealthTodayTabComponent', () => {
  let health: jasmine.SpyObj<HealthService>;

  function render(today: HealthToday) {
    health.getToday.and.returnValue(of(today));
    const fixture = TestBed.createComponent(HealthTodayTabComponent);
    fixture.detectChanges();
    fixture.componentInstance.ngOnChanges();
    fixture.detectChanges();
    return fixture;
  }

  beforeEach(() => {
    health = jasmine.createSpyObj<HealthService>('HealthService', ['getToday']);
    TestBed.configureTestingModule({
      imports: [HealthTodayTabComponent],
      providers: [{ provide: HealthService, useValue: health }],
    });
  });

  it('shows an empty state with a way to log a day when there is no data', () => {
    const fixture = render({ day: null, is_today: false, metrics: [] });
    const logged = jasmine.createSpy('log');
    fixture.componentInstance.logDay.subscribe(logged);

    fixture.nativeElement.querySelector('[data-testid="health-today-log-button"]').click();

    expect(fixture.nativeElement.querySelector('[data-testid="health-today-empty"]')).not.toBeNull();
    expect(logged).toHaveBeenCalledTimes(1);
  });

  it('shows the value, both averages and the marker in words, not colour alone', () => {
    const fixture = render({
      day: '2026-05-19',
      is_today: false,
      metrics: [metric({}), metric({ key: 'hrv_ms', label: 'HRV', unit: 'ms', value: 50, marker: 'flat', favourable: null })] as never,
    });
    const text = (fixture.nativeElement as HTMLElement).textContent as string;

    expect(text).toContain('Latest data:');
    expect(text).toContain('58 bpm');
    expect(text).toContain('▲ above your 30-day average (worse)');
    expect(text).toContain('7-day average 53 bpm · 30-day average 52 bpm');
    expect(text).toContain('● in line with your 30-day average');
  });

  it('says more data is needed when there is no baseline yet', () => {
    const fixture = render({
      day: '2026-05-19',
      is_today: true,
      metrics: [metric({ avg_7d: null, avg_30d: null, marker: null, favourable: null, needs_more_data: true })] as never,
    });
    const text = (fixture.nativeElement as HTMLElement).textContent as string;

    expect(text).toContain('Today,');
    expect(text).toContain('More data needed for a comparison');
  });
});
