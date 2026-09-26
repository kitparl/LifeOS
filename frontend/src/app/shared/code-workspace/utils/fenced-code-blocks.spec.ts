import {
  codeBlockFirstLine,
  matchRenderedFences,
  parseFencedCodeBlocks,
} from './fenced-code-blocks';

describe('matchRenderedFences', () => {
  it('matches rendered fences to parsed blocks in order, including duplicate code', () => {
    const blocks = parseFencedCodeBlocks(
      '```py\nprint(1)\n```\n\n```js\nconsole.log(1)\n```\n\n```py\nprint(1)\n```'
    );
    const matched = matchRenderedFences(
      [
        { language: 'py', code: 'print(1)\n' },
        { language: 'js', code: 'console.log(1)\n' },
        { language: 'py', code: 'print(1)\n' },
      ],
      blocks
    );
    expect(matched).toEqual([blocks[0], blocks[1], blocks[2]]);
  });

  it('treats language aliases as equal', () => {
    const blocks = parseFencedCodeBlocks('```python\nx = 1\n```');
    expect(matchRenderedFences([{ language: 'py', code: 'x = 1' }], blocks)).toEqual([blocks[0]]);
  });

  it('returns null for a fence the parser skipped without shifting later matches', () => {
    const markdown = '```python title\nskipped()\n```\n\n```py\nkept()\n```';
    const blocks = parseFencedCodeBlocks(markdown);
    expect(blocks.length).toBe(1);
    const matched = matchRenderedFences(
      [
        { language: 'python', code: 'skipped()\n' },
        { language: 'py', code: 'kept()\n' },
      ],
      blocks
    );
    expect(matched).toEqual([null, blocks[0]]);
  });

  it('does not match when the language differs', () => {
    const blocks = parseFencedCodeBlocks('```js\n1\n```');
    expect(matchRenderedFences([{ language: 'sql', code: '1' }], blocks)).toEqual([null]);
  });
});

describe('codeBlockFirstLine', () => {
  it('returns the first non-empty line, truncated', () => {
    expect(codeBlockFirstLine('\n  print(1)\nprint(2)')).toBe('print(1)');
    expect(codeBlockFirstLine('x'.repeat(50), 10)).toBe('xxxxxxxxx…');
  });
});
