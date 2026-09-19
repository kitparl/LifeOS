import { explainCron, buildCronExpression } from './cron.util';

describe('cron.util', () => {
  it('explains a simple daily schedule', () => {
    expect(explainCron('30 9 * * *')).toBe('At 09:30.');
  });

  it('explains a step expression', () => {
    expect(explainCron('*/15 * * * *')).toContain('every 15 minutes');
  });

  it('explains day-of-week names', () => {
    expect(explainCron('0 9 * * 1-5')).toContain('Monday through Friday');
  });

  it('rejects the wrong number of fields', () => {
    expect(() => explainCron('* * *')).toThrowError(/5 space-separated fields/);
  });

  it('rejects invalid characters', () => {
    expect(() => explainCron('a * * * *')).toThrowError();
  });

  it('builds a cron expression from fields', () => {
    expect(buildCronExpression({ minute: '0', hour: '9', dayOfMonth: '*', month: '*', dayOfWeek: '1-5' })).toBe('0 9 * * 1-5');
  });
});
