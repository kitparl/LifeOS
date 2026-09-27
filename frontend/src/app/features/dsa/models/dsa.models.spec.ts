import { difficultyTone, formatJson, isTerminal, verdictTone } from './dsa.models';

describe('dsa model helpers', () => {
  it('detects terminal job statuses', () => {
    expect(isTerminal('done')).toBeTrue();
    expect(isTerminal('error')).toBeTrue();
    expect(isTerminal('pending')).toBeFalse();
    expect(isTerminal('running')).toBeFalse();
  });

  it('maps verdicts and difficulty to badge tones', () => {
    expect(verdictTone('Accepted')).toBe('success');
    expect(verdictTone('Wrong Answer')).toBe('danger');
    expect(verdictTone('Time Limit Exceeded')).toBe('warning');
    expect(verdictTone('Internal Error')).toBe('info');
    expect(verdictTone(null)).toBe('default');
    expect(difficultyTone('easy')).toBe('success');
    expect(difficultyTone('hard')).toBe('danger');
  });

  it('formats JSON compactly', () => {
    expect(formatJson([[1, 2], 'a', null])).toBe('[[1,2],"a",null]');
    expect(formatJson(undefined)).toBe('');
  });
});
