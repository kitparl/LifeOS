import { PeriodPreset, PeriodSelection } from '../models/finance.models';

export const PERIOD_OPTIONS: { value: PeriodPreset; label: string }[] = [
  { value: 'this_month', label: 'This Month' },
  { value: 'last_month', label: 'Last Month' },
  { value: 'this_year', label: 'This Year' },
  { value: 'custom', label: 'Custom Period' },
];

export function todayIso(): string {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

export function startOfMonthIso(): string {
  return `${todayIso().slice(0, 7)}-01`;
}

/** Default selection: the current calendar month, whether or not it has activity. */
export function defaultPeriod(): PeriodSelection {
  return { preset: 'this_month' };
}
