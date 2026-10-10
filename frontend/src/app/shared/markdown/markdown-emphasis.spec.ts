import { toggleMarkdownEmphasis } from './markdown-emphasis';

describe('toggleMarkdownEmphasis', () => {
  it('wraps the selection in bold markers and keeps the inner text selected', () => {
    expect(toggleMarkdownEmphasis('use indexes here', 4, 11, 'bold')).toEqual({
      value: 'use **indexes** here',
      selectionStart: 6,
      selectionEnd: 13,
    });
  });

  it('removes bold markers when pressed again', () => {
    expect(toggleMarkdownEmphasis('use **indexes** here', 6, 13, 'bold')).toEqual({
      value: 'use indexes here',
      selectionStart: 4,
      selectionEnd: 11,
    });
  });

  it('toggles italic on and off', () => {
    const on = toggleMarkdownEmphasis('a word', 2, 6, 'italic');
    expect(on.value).toBe('a *word*');
    expect(toggleMarkdownEmphasis(on.value, on.selectionStart, on.selectionEnd, 'italic').value).toBe('a word');
  });

  it('combines italic with existing bold and removes each independently', () => {
    const both = toggleMarkdownEmphasis('**x**', 2, 3, 'italic');
    expect(both.value).toBe('***x***');
    expect(toggleMarkdownEmphasis(both.value, both.selectionStart, both.selectionEnd, 'bold').value).toBe('*x*');
    expect(toggleMarkdownEmphasis(both.value, both.selectionStart, both.selectionEnd, 'italic').value).toBe('**x**');
  });

  it('inserts empty markers with the caret between them when nothing is selected', () => {
    expect(toggleMarkdownEmphasis('ab', 1, 1, 'bold')).toEqual({ value: 'a****b', selectionStart: 3, selectionEnd: 3 });
  });
});
