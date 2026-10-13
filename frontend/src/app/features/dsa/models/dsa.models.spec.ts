import {
  SignatureSpec,
  difficultyTone,
  formatJson,
  inputFields,
  isTerminal,
  joinInput,
  parseJson,
  splitInput,
  verdictTone,
} from './dsa.models';

const FN: SignatureSpec = {
  kind: 'function',
  name: 'twoSum',
  params: [
    { name: 'nums', type: 'int[]' },
    { name: 'target', type: 'int' },
  ],
  returns: 'int[]',
};
const DESIGN: SignatureSpec = { kind: 'class', name: 'LRUCache', constructor: [], methods: [] };

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

  it('parses JSON text, or returns undefined when invalid', () => {
    expect<unknown>(parseJson('[1, 2]')).toEqual([1, 2]);
    expect(parseJson('null')).toBeNull();
    expect(parseJson('[1,')).toBeUndefined();
    expect(parseJson('')).toBeUndefined();
  });

  it('splits a function input into one value per parameter and joins it back', () => {
    expect(inputFields(FN)).toEqual([
      { name: 'nums', type: 'int[]' },
      { name: 'target', type: 'int' },
    ]);
    expect<unknown>(splitInput(FN, [[2, 7], 9])).toEqual([[2, 7], 9]);
    expect<unknown>(splitInput(FN, [[2, 7]])).toBeNull();
    expect<unknown>(joinInput(FN, [[2, 7], 9])).toEqual([[2, 7], 9]);
  });

  it('splits a design input into ops and args', () => {
    const input = { ops: ['LRUCache', 'get'], args: [[2], [1]] };
    expect(inputFields(DESIGN).map((f) => f.name)).toEqual(['ops', 'args']);
    expect<unknown>(splitInput(DESIGN, input)).toEqual([input.ops, input.args]);
    expect<unknown>(joinInput(DESIGN, [input.ops, input.args])).toEqual(input);
    expect<unknown>(splitInput(DESIGN, [1])).toBeNull();
  });

  it('treats an input with no described params as one raw JSON field', () => {
    expect(inputFields(null)).toEqual([{ name: 'input', type: 'JSON' }]);
    expect<unknown>(splitInput(null, [1, 2])).toEqual([[1, 2]]);
    expect<unknown>(joinInput(null, [[1, 2]])).toEqual([1, 2]);
  });
});
