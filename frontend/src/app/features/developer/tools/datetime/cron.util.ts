const MONTH_NAMES = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const DOW_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

function validateField(field: string, label: string): void {
  if (!/^[\d*/,-]+$/.test(field)) {
    throw new Error(`Invalid ${label} field "${field}" — only digits, *, /, ,, and - are supported.`);
  }
}

function joinList(items: string[]): string {
  if (items.length === 1) return items[0];
  return items.slice(0, -1).join(', ') + ' and ' + items[items.length - 1];
}

function describeField(value: string, unit: string, names?: string[]): string {
  const label = (n: string): string => (names ? names[Number(n)] ?? n : n);
  if (value === '*') return `every ${unit}`;
  if (value.includes('/')) {
    const [range, step] = value.split('/');
    return `every ${step} ${unit}${step === '1' ? '' : 's'}${range !== '*' ? ` starting at ${label(range)}` : ''}`;
  }
  if (value.includes(',')) {
    return joinList(value.split(',').map(label));
  }
  if (value.includes('-')) {
    const [start, end] = value.split('-');
    return `${unit}s ${label(start)} through ${label(end)}`;
  }
  return label(value);
}

/** Parses and explains a standard 5-field cron expression (minute hour day-of-month month day-of-week) in plain English. */
export function explainCron(expr: string): string {
  const fields = expr.trim().split(/\s+/);
  if (fields.length !== 5) {
    throw new Error(`Expected 5 space-separated fields (minute hour day-of-month month day-of-week), got ${fields.length}.`);
  }
  const [min, hour, dom, mon, dow] = fields;
  validateField(min, 'minute');
  validateField(hour, 'hour');
  validateField(dom, 'day-of-month');
  validateField(mon, 'month');
  validateField(dow, 'day-of-week');

  const isPlainNumber = (v: string): boolean => /^\d+$/.test(v);
  let timePhrase: string;
  if (isPlainNumber(min) && isPlainNumber(hour)) {
    timePhrase = `at ${hour.padStart(2, '0')}:${min.padStart(2, '0')}`;
  } else {
    timePhrase = `at minute ${describeField(min, 'minute')} of hour ${describeField(hour, 'hour')}`;
  }

  const parts = [timePhrase];
  if (dom !== '*') parts.push(`on day-of-month ${describeField(dom, 'day')}`);
  if (mon !== '*') parts.push(`in ${describeField(mon, 'month', MONTH_NAMES)}`);
  if (dow !== '*') parts.push(`on ${describeField(dow, 'day', DOW_NAMES)}`);

  const sentence = parts.join(', ');
  return sentence[0].toUpperCase() + sentence.slice(1) + '.';
}

export interface CronFields {
  minute: string;
  hour: string;
  dayOfMonth: string;
  month: string;
  dayOfWeek: string;
}

export function buildCronExpression(f: CronFields): string {
  return `${f.minute} ${f.hour} ${f.dayOfMonth} ${f.month} ${f.dayOfWeek}`;
}
