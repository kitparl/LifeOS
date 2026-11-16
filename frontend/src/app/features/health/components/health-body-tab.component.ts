import { DatePipe } from '@angular/common';
import { Component, Input, OnChanges, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Observable, forkJoin } from 'rxjs';
import { localIsoDate, toDatetimeLocalValue } from '../../../core/utils/date';
import { apiErrorMessage } from '../../../core/utils/http';
import { ChartPoint } from '../../../shared/charts/chart-types';
import { LineChartComponent } from '../../../shared/charts/line-chart.component';
import { ConfirmService } from '../../../shared/confirm/confirm.service';
import { cleanMessage } from '../health.utils';
import { Measurement } from '../models/health.models';
import { HealthService } from '../services/health.service';

const WINDOW_DAYS = 90;

/** Weight and body composition over time, plus blood pressure readings. */
@Component({
  selector: 'app-health-body-tab',
  standalone: true,
  imports: [ReactiveFormsModule, DatePipe, LineChartComponent],
  host: { class: 'contents' },
  template: `
    <div class="grid gap-3 md:grid-cols-2">
      <div class="panel space-y-1" data-testid="health-body-latest">
        <p class="text-xs" style="color: var(--text-muted)">Latest weight</p>
        <p class="text-xl font-semibold">{{ latestWeight() ?? '—' }}@if (latestWeight() !== null) { kg }</p>
        @if (latestBodyFat() !== null) {
          <p class="text-xs" style="color: var(--text-muted)">Body fat {{ latestBodyFat() }}%</p>
        }
      </div>
      <div class="panel space-y-1">
        <p class="text-xs" style="color: var(--text-muted)">Weight, last {{ windowDays }} days</p>
        @if (weightPoints().length > 1) {
          <app-line-chart [points]="weightPoints()" title="Weight over the last 90 days" [width]="480" [height]="140" [fitRange]="true" />
        } @else {
          <p class="text-sm" style="color: var(--text-muted)">Add weigh-ins to see a chart.</p>
        }
      </div>
    </div>

    <div class="grid gap-3 md:grid-cols-2">
      <form class="panel space-y-2 text-sm" [formGroup]="weighForm" (ngSubmit)="addWeighIn()" data-testid="health-weigh-form">
        <p class="font-medium">Weigh-in</p>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="form-label" for="weigh-kg">Weight (kg)</label>
            <input id="weigh-kg" class="input-field mt-1" type="number" step="0.1" formControlName="weight_kg" data-testid="health-weigh-kg-input" />
          </div>
          <div>
            <label class="form-label" for="weigh-fat">Body fat % (optional)</label>
            <input id="weigh-fat" class="input-field mt-1" type="number" step="0.1" formControlName="body_fat_pct" data-testid="health-weigh-fat-input" />
          </div>
        </div>
        <div>
          <label class="form-label" for="weigh-when">When</label>
          <input id="weigh-when" class="input-field mt-1" type="datetime-local" formControlName="when" />
        </div>
        <button type="submit" class="btn-primary text-xs" data-testid="health-weigh-save-button" [disabled]="weighForm.invalid || busy()">Save weigh-in</button>
      </form>

      <form class="panel space-y-2 text-sm" [formGroup]="pressureForm" (ngSubmit)="addPressure()" data-testid="health-pressure-form">
        <p class="font-medium">Blood pressure</p>
        <div class="grid grid-cols-3 gap-2">
          <div>
            <label class="form-label" for="bp-sys">Systolic</label>
            <input id="bp-sys" class="input-field mt-1" type="number" formControlName="systolic" data-testid="health-bp-systolic-input" />
          </div>
          <div>
            <label class="form-label" for="bp-dia">Diastolic</label>
            <input id="bp-dia" class="input-field mt-1" type="number" formControlName="diastolic" data-testid="health-bp-diastolic-input" />
          </div>
          <div>
            <label class="form-label" for="bp-pulse">Pulse</label>
            <input id="bp-pulse" class="input-field mt-1" type="number" formControlName="pulse" />
          </div>
        </div>
        <button type="submit" class="btn-primary text-xs" data-testid="health-bp-save-button" [disabled]="pressureForm.invalid || busy()">Save reading</button>
      </form>
    </div>

    @if (error()) {
      <p class="text-xs" style="color: var(--danger)" data-testid="health-body-error">{{ error() }}</p>
    }

    <div class="panel !p-0 overflow-hidden">
      @if (!readings().length) {
        <div class="empty-state"><p class="empty-state__title">No readings in the last {{ windowDays }} days</p></div>
      } @else {
        <ul data-testid="health-body-readings">
          @for (r of readings(); track r.id) {
            <li class="flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-sm" style="border-bottom: 1px solid var(--border)">
              <span>
                {{ r.measured_at | date: 'medium' }}
                <span style="color: var(--text-muted)"> · {{ describe(r) }}</span>
              </span>
              <button type="button" class="link text-xs" style="color: var(--danger)" [attr.data-testid]="'health-reading-delete-' + r.id" (click)="remove(r)">Delete</button>
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class HealthBodyTabComponent implements OnInit, OnChanges {
  private readonly health = inject(HealthService);
  private readonly fb = inject(FormBuilder);
  private readonly confirm = inject(ConfirmService);

  @Input() refresh = 0;

  readonly windowDays = WINDOW_DAYS;
  readonly readings = signal<Measurement[]>([]);
  readonly weightPoints = signal<ChartPoint[]>([]);
  readonly latestWeight = signal<number | null>(null);
  readonly latestBodyFat = signal<number | null>(null);
  readonly busy = signal(false);
  readonly error = signal('');

  readonly weighForm = this.fb.group({
    weight_kg: this.fb.control<number | null>(null, [Validators.required, Validators.min(20), Validators.max(400)]),
    body_fat_pct: this.fb.control<number | null>(null, [Validators.min(1), Validators.max(80)]),
    when: this.fb.nonNullable.control(toDatetimeLocalValue(new Date())),
  });

  readonly pressureForm = this.fb.group({
    systolic: this.fb.control<number | null>(null, [Validators.required, Validators.min(50), Validators.max(260)]),
    diastolic: this.fb.control<number | null>(null, [Validators.required, Validators.min(30), Validators.max(160)]),
    pulse: this.fb.control<number | null>(null, [Validators.min(20), Validators.max(250)]),
  });

  ngOnInit(): void {
    this.load();
  }

  ngOnChanges(changes: { refresh?: unknown }): void {
    if (changes.refresh && this.readings().length) this.load();
  }

  describe(r: Measurement): string {
    const v = r.values;
    if (r.kind === 'weight') return `Weight ${v['weight_kg']} kg`;
    if (r.kind === 'body_comp') {
      return [
        v['body_fat_pct'] !== undefined ? `body fat ${v['body_fat_pct']}%` : null,
        v['muscle_mass_kg'] !== undefined ? `muscle ${v['muscle_mass_kg']} kg` : null,
        v['bmi'] !== undefined ? `BMI ${v['bmi']}` : null,
      ]
        .filter(Boolean)
        .join(', ');
    }
    return `Blood pressure ${v['systolic']}/${v['diastolic']}${v['pulse'] !== undefined ? `, pulse ${v['pulse']}` : ''}`;
  }

  addWeighIn(): void {
    if (this.weighForm.invalid) return;
    const raw = this.weighForm.getRawValue();
    const when = raw.when ? new Date(raw.when).toISOString() : null;
    const requests: Observable<Measurement>[] = [
      this.health.addMeasurement({ kind: 'weight', measured_at: when, values: { weight_kg: raw.weight_kg as number } }),
    ];
    if (raw.body_fat_pct !== null) {
      requests.push(this.health.addMeasurement({ kind: 'body_comp', measured_at: when, values: { body_fat_pct: raw.body_fat_pct } }));
    }
    this.save(requests, () => this.weighForm.patchValue({ weight_kg: null, body_fat_pct: null, when: toDatetimeLocalValue(new Date()) }));
  }

  addPressure(): void {
    if (this.pressureForm.invalid) return;
    const raw = this.pressureForm.getRawValue();
    const values: Record<string, number> = { systolic: raw.systolic as number, diastolic: raw.diastolic as number };
    if (raw.pulse !== null) values['pulse'] = raw.pulse;
    this.save([this.health.addMeasurement({ kind: 'blood_pressure', values })], () =>
      this.pressureForm.reset({ systolic: null, diastolic: null, pulse: null }),
    );
  }

  async remove(reading: Measurement): Promise<void> {
    const ok = await this.confirm.confirm('Delete this reading?');
    if (!ok) return;
    this.health.deleteMeasurement(reading.id).subscribe({
      next: () => this.load(),
      error: (err) => this.error.set(cleanMessage(apiErrorMessage(err, 'The reading could not be deleted'))),
    });
  }

  private save(requests: Observable<Measurement>[], reset: () => void): void {
    this.busy.set(true);
    this.error.set('');
    forkJoin(requests).subscribe({
      next: () => {
        reset();
        this.busy.set(false);
        this.load();
      },
      error: (err) => {
        this.error.set(cleanMessage(apiErrorMessage(err, 'The reading could not be saved')));
        this.busy.set(false);
      },
    });
  }

  private load(): void {
    const end = localIsoDate();
    const start = localIsoDate(new Date(Date.now() - WINDOW_DAYS * 86_400_000));
    forkJoin({
      weight: this.health.listMeasurements('weight', start, end),
      bodyComp: this.health.listMeasurements('body_comp', start, end),
      pressure: this.health.listMeasurements('blood_pressure', start, end),
    }).subscribe({
      next: ({ weight, bodyComp, pressure }) => {
        const newestFirst = [...weight, ...bodyComp, ...pressure].sort((a, b) => b.measured_at.localeCompare(a.measured_at));
        this.readings.set(newestFirst);
        const oldestFirst = [...weight].reverse();
        this.weightPoints.set(
          oldestFirst.map((w) => ({ label: w.measured_at.slice(0, 10), value: w.values['weight_kg'] })),
        );
        this.latestWeight.set(weight[0]?.values['weight_kg'] ?? null);
        this.latestBodyFat.set(bodyComp.find((m) => m.values['body_fat_pct'] !== undefined)?.values['body_fat_pct'] ?? null);
      },
      error: () => this.error.set('Readings could not be loaded.'),
    });
  }
}
