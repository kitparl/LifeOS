import { combineDueDate, localDateInputValue, splitDueDate } from './task-due-date.util';

describe('task-due-date.util', () => {
  it('combines date-only as noon local', () => {
    const iso = combineDueDate('2026-08-22', '');
    expect(iso).toBeTruthy();
    const d = new Date(iso!);
    expect(d.getHours()).toBe(12);
    expect(d.getMinutes()).toBe(0);
  });

  it('combines date and time', () => {
    const iso = combineDueDate('2026-08-22', '09:30');
    const d = new Date(iso!);
    expect(d.getHours()).toBe(9);
    expect(d.getMinutes()).toBe(30);
  });

  it('returns null when date cleared', () => {
    expect(combineDueDate('', '09:00')).toBeNull();
  });

  it('splits noon-only due dates without time field', () => {
    const noon = combineDueDate('2026-08-22', '')!;
    expect(splitDueDate(noon)).toEqual({ date: '2026-08-22', time: '' });
  });

  it('formats today for date input', () => {
    expect(localDateInputValue(new Date(2026, 7, 22))).toBe('2026-08-22');
  });
});
