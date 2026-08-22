import { sanitizeMarkdownFilename, downloadMarkdown } from './markdown-export';

describe('markdown-export', () => {
  it('sanitizeMarkdownFilename strips unsafe characters and adds .md', () => {
    expect(sanitizeMarkdownFilename('My Section')).toBe('My-Section.md');
    expect(sanitizeMarkdownFilename('')).toBe('export.md');
    expect(sanitizeMarkdownFilename('notes.md')).toBe('notes.md');
  });

  it('downloadMarkdown rejects empty content', () => {
    expect(() => downloadMarkdown('', 'test')).toThrowError('Nothing to export.');
    expect(() => downloadMarkdown('   \n  ', 'test')).toThrowError('Nothing to export.');
  });

  it('downloadMarkdown triggers a download link', () => {
    const clickSpy = jasmine.createSpy('click');
    const link = document.createElement('a');
    spyOn(document, 'createElement').and.returnValue(link);
    spyOn(link, 'click').and.callFake(clickSpy);
    spyOn(URL, 'createObjectURL').and.returnValue('blob:test');
    spyOn(URL, 'revokeObjectURL');

    downloadMarkdown('# Hello', 'test');

    expect(link.download).toBe('test.md');
    expect(clickSpy).toHaveBeenCalled();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:test');
  });
});
