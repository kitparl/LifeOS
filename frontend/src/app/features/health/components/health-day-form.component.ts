import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, inject, signal } from '@angular/core';
import { localIsoDate } from '../../../core/utils/date';
import { apiErrorMessage } from '../../../core/utils/http';
import { ModalComponent } from '../../../shared/modal/modal.component';
import { buildDayPayload, cleanMessage, fieldText, formatMetric, manualValues } from '../health.utils';
import { METRIC_GROUPS, MetricInfo } from '../models/health.models';
import { HealthService } from '../services/health.service';

/** Enter or correct the values of one day. Only filled fields are saved; blank leaves a value as it is. */
@Component({
  selector: 'app-health-day-form',
  standalone: true,
  imports: [ModalComponent],
  template: `
    <app-modal [open]="open" title="Log a day" [maxWidth]="'640px'" (closed)="closed.emit()">
      <div body class="space-y-3 text-sm">
        <div>
          <label class="form-label" for="health-day-date">Date</label>
          <input
            id="health-day-date"
            class="input-field mt-1"
            style="max-width: 12rem"
            type="date"
            data-testid="health-day-date-input"
            [value]="date()"
            [max]="maxDate"
            (change)="onDate($event)"
          />
        </div>
        @for (g of groups; track g.id) {
          <fieldset class="space-y-2">
            <legend class="text-xs font-semibold" style="color: var(--text-muted)">{{ g.label }}</legend>
            <div class="grid gap-2 sm:grid-cols-2">
              @for (m of metricsOf(g.id); track m.key) {
                <div>
                  <label class="form-label" [for]="'health-day-' + m.key">{{ m.label }}@if (m.unit) { ({{ m.unit }}) }</label>
                  <input
                    [id]="'health-day-' + m.key"
                    class="input-field mt-1"
                    [attr.type]="m.kind === 'clock' ? 'time' : 'number'"
                    [attr.step]="m.kind === 'float' ? 'any' : m.kind === 'int' ? '1' : null"
                    [attr.min]="m.kind === 'clock' ? null : m.min"
                    [attr.max]="m.kind === 'clock' ? null : m.max"
                    [attr.data-testid]="'health-day-' + m.key"
                    [value]="texts()[m.key] ?? ''"
                    (input)="setText(m.key, $event)"
                  />
                  @if (hints()[m.key] !== undefined) {
                    <p class="text-xs mt-0.5" style="color: var(--text-muted)">Garmin: {{ show(m, hints()[m.key]) }}</p>
                  }
                </div>
              }
            </div>
          </fieldset>
        }
        @if (error()) {
          <p class="text-xs" style="color: var(--danger)" data-testid="health-day-error">{{ error() }}</p>
        }
      </div>
      <div footer class="flex flex-wrap justify-end gap-2">
        <button type="button" class="btn-secondary text-xs" data-testid="health-day-cancel-button" (click)="closed.emit()">Cancel</button>
        <button type="button" class="btn-primary text-xs" data-testid="health-day-save-button" [disabled]="busy()" (click)="save()">
          {{ busy() ? 'Saving…' : 'Save day' }}
        </button>
      </div>
    </app-modal>
  `,
})
export class HealthDayFormComponent implements OnChanges {
  private readonly health = inject(HealthService);

  @Input() open = false;
  @Input({ required: true }) catalogue: MetricInfo[] = [];
  @Output() readonly closed = new EventEmitter<void>();
  @Output() readonly saved = new EventEmitter<void>();

  readonly groups = METRIC_GROUPS;
  readonly maxDate = localIsoDate();
  readonly date = signal(localIsoDate());
  readonly texts = signal<Record<string, string>>({});
  /** Values an import stored for the day; shown as hints, never copied into the form. */
  readonly hints = signal<Record<string, number>>({});
  readonly busy = signal(false);
  readonly error = signal('');

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['open']?.currentValue === true) {
      this.date.set(localIsoDate());
      this.error.set('');
      this.loadDay();
    }
  }

  metricsOf(group: string): MetricInfo[] {
    return this.catalogue.filter((m) => m.group === group);
  }

  show(metric: MetricInfo, value: number): string {
    return formatMetric(metric, value);
  }

  setText(key: string, event: Event): void {
    this.texts.update((t) => ({ ...t, [key]: (event.target as HTMLInputElement).value }));
  }

  onDate(event: Event): void {
    this.date.set((event.target as HTMLInputElement).value);
    this.error.set('');
    this.loadDay();
  }

  save(): void {
    const { values, invalid } = buildDayPayload(this.texts(), this.catalogue);
    if (invalid.length) {
      this.error.set(`Check these fields: ${invalid.join(', ')}`);
      return;
    }
    if (!Object.keys(values).length) {
      this.error.set('Enter at least one value.');
      return;
    }
    this.busy.set(true);
    this.error.set('');
    this.health.saveDay(this.date(), values).subscribe({
      next: () => {
        this.busy.set(false);
        this.saved.emit();
      },
      error: (err) => {
        this.error.set(cleanMessage(apiErrorMessage(err, 'The day could not be saved')));
        this.busy.set(false);
      },
    });
  }

  private loadDay(): void {
    this.texts.set({});
    this.hints.set({});
    this.health.getDay(this.date()).subscribe({
      next: (day) => {
        const mine = manualValues(day);
        this.texts.set(Object.fromEntries(this.catalogue.filter((m) => m.key in mine).map((m) => [m.key, fieldText(m, mine[m.key])])));
        this.hints.set(Object.fromEntries(Object.entries(day.values).filter(([key]) => day.sources[key] !== 'manual')));
      },
      error: () => undefined, // no data for this day yet: the form stays blank
    });
  }
}
