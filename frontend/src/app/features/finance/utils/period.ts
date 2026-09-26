import { PeriodSelection } from '../models/finance.models';
import { localIsoDate, pad2 } from '../../../core/utils/date';

/** 0 means every month in the selected year. */
export const ALL_MONTHS = 0;

export function startOfMonthIso(now = new Date()): string {
  return `${localIsoDate(now).slice(0, 7)}-01`;
}

export function currentYear(now = new Date()): number {
  return now.getFullYear();
}

export function currentMonth(now = new Date()): number {
  return now.getMonth() + 1;
}

export function yearOptions(now = new Date()): number[] {
  const end = currentYear(now);
  const start = end - 10;
  const years: number[] = [];
  for (let year = end; year >= start; year -= 1) years.push(year);
  return years;
}

export function lastDayOfMonthIso(year: number, month: number): string {
  const day = new Date(year, month, 0).getDate();
  return `${year}-${pad2(month)}-${pad2(day)}`;
}

/** Default selection: the current calendar month, whether or not it has activity. */
export function defaultPeriod(now = new Date()): PeriodSelection {
  return periodFromYearMonth(currentYear(now), currentMonth(now), now);
}

export function periodFromYearMonth(
  year: number,
  month: number,
  now = new Date(),
): PeriodSelection {
  if (month === ALL_MONTHS) {
    if (year === currentYear(now)) return { preset: 'this_year' };
    return { preset: 'custom', start: `${year}-01-01`, end: `${year}-12-31` };
  }

  if (year === currentYear(now) && month === currentMonth(now)) {
    return { preset: 'this_month' };
  }

  return {
    preset: 'custom',
    start: `${year}-${pad2(month)}-01`,
    end: lastDayOfMonthIso(year, month),
  };
}
