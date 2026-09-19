/** Calendar months in display order. Index 0 is January (month number 1). */
export const MONTH_NAMES = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
] as const;

export type MonthName = (typeof MONTH_NAMES)[number];

export interface MonthOption {
  value: number;
  label: MonthName;
}

/** 1–12 options for month dropdowns. */
export const MONTH_OPTIONS: MonthOption[] = MONTH_NAMES.map((label, index) => ({
  value: index + 1,
  label,
}));
