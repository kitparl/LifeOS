import { Component, EventEmitter, Input, Output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MONTH_OPTIONS } from '../../../core/constants/months';
import { PeriodSelection } from '../models/finance.models';
import {
  ALL_MONTHS,
  currentMonth,
  currentYear,
  periodFromYearMonth,
  yearOptions,
} from '../utils/period';

/**
 * Year + month selector for the whole Finance module. Defaults to the current
 * calendar month. "All months" covers the selected year.
 */
@Component({
  selector: 'app-finance-period-filter',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="flex flex-wrap items-center gap-2 text-xs" style="color: var(--text-muted)">
      <label class="flex items-center gap-1.5" for="finance-year-select">
        <span>Year:</span>
        <select
          id="finance-year-select"
          class="input-field !w-auto !py-1 text-xs"
          data-testid="finance-year-filter"
          [ngModel]="year()"
          (ngModelChange)="setYear($event)"
        >
          @for (option of years; track option) {
            <option [ngValue]="option">{{ option }}</option>
          }
        </select>
      </label>

      <label class="flex items-center gap-1.5" for="finance-month-select">
        <span>Month:</span>
        <select
          id="finance-month-select"
          class="input-field !w-auto !py-1 text-xs"
          data-testid="finance-month-filter"
          [ngModel]="month()"
          (ngModelChange)="setMonth($event)"
        >
          <option [ngValue]="allMonths">All months</option>
          @for (option of monthOptions; track option.value) {
            <option [ngValue]="option.value">{{ option.label }}</option>
          }
        </select>
      </label>
    </div>
  `,
})
export class PeriodFilterComponent {
  @Input({ required: true }) period!: PeriodSelection;
  @Output() readonly periodChange = new EventEmitter<PeriodSelection>();

  readonly allMonths = ALL_MONTHS;
  readonly monthOptions = MONTH_OPTIONS;
  readonly years = yearOptions();
  readonly year = signal(currentYear());
  readonly month = signal(currentMonth());

  setYear(year: number): void {
    this.year.set(Number(year));
    this.emit();
  }

  setMonth(month: number): void {
    this.month.set(Number(month));
    this.emit();
  }

  private emit(): void {
    this.periodChange.emit(periodFromYearMonth(this.year(), this.month()));
  }
}
