import {
  MAX_MARKDOWN_IMPORT_BYTES,
  extractFirstHeading,
  hasMarkdownContent,
  isMarkdownFile,
  mergeMarkdownContent,
  suggestTitleFromImport,
  titleFromFilename,
  validateMarkdownFile,
} from './markdown-import';

describe('markdown-import', () => {
  function file(name: string, type: string, size: number, content = ''): File {
    const blob = new Blob([content], { type });
    return new File([blob], name, { type });
  }

  describe('validateMarkdownFile', () => {
    it('accepts .md files', () => {
      expect(validateMarkdownFile(file('notes.md', 'text/markdown', 12, '# Hi'))).toBeNull();
    });

    it('accepts plain text files', () => {
      expect(validateMarkdownFile(file('notes.txt', 'text/plain', 8, 'hello'))).toBeNull();
    });

    it('rejects non-text files', () => {
      const pdf = file('doc.pdf', 'application/pdf', 100);
      expect(validateMarkdownFile(pdf)).toContain('markdown');
    });

    it('rejects empty files', () => {
      expect(validateMarkdownFile(file('empty.md', 'text/markdown', 0))).toContain('empty');
    });

    it('rejects files over 2MB', () => {
      const big = file(
        'big.md',
        'text/markdown',
        MAX_MARKDOWN_IMPORT_BYTES + 1,
        'x'.repeat(MAX_MARKDOWN_IMPORT_BYTES + 1)
      );
      expect(validateMarkdownFile(big)).toContain('too large');
    });
  });

  describe('isMarkdownFile', () => {
    it('recognizes markdown extensions and mime types', () => {
      expect(isMarkdownFile(file('a.md', 'application/octet-stream', 1))).toBeTrue();
      expect(isMarkdownFile(file('a.txt', 'text/markdown', 1))).toBeTrue();
      expect(isMarkdownFile(file('a.txt', 'text/plain', 1))).toBeTrue();
    });
  });

  describe('mergeMarkdownContent', () => {
    it('replaces existing content', () => {
      expect(mergeMarkdownContent('old', 'new', 'replace')).toBe('new');
    });

    it('appends with blank line separator', () => {
      expect(mergeMarkdownContent('existing', 'imported', 'append')).toBe('existing\n\nimported');
    });

    it('append on empty current content returns imported only', () => {
      expect(mergeMarkdownContent('', 'imported', 'append')).toBe('imported');
      expect(mergeMarkdownContent('   ', 'imported', 'append')).toBe('imported');
    });
  });

  describe('hasMarkdownContent', () => {
    it('treats whitespace-only as empty', () => {
      expect(hasMarkdownContent('')).toBeFalse();
      expect(hasMarkdownContent('  \n  ')).toBeFalse();
      expect(hasMarkdownContent('text')).toBeTrue();
    });
  });

  describe('extractFirstHeading', () => {
    it('returns first ATX heading text', () => {
      expect(extractFirstHeading('# My Title\n\nBody')).toBe('My Title');
      expect(extractFirstHeading('intro\n# Second')).toBe('Second');
    });

    it('returns null when no heading', () => {
      expect(extractFirstHeading('plain text')).toBeNull();
    });
  });

  describe('titleFromFilename', () => {
    it('strips .md extension', () => {
      expect(titleFromFilename('my-notes.md')).toBe('my-notes');
    });
  });

  describe('suggestTitleFromImport', () => {
    it('prefers first heading when title is untitled', () => {
      expect(suggestTitleFromImport('file.md', '# Imported Title\n\nBody', '')).toBe(
        'Imported Title'
      );
      expect(suggestTitleFromImport('file.md', '# Imported Title\n\nBody', 'Untitled')).toBe(
        'Imported Title'
      );
    });

    it('falls back to filename without extension', () => {
      expect(suggestTitleFromImport('my-notes.md', 'no heading', '')).toBe('my-notes');
    });

    it('returns null when title already set', () => {
      expect(suggestTitleFromImport('file.md', '# Heading', 'Existing')).toBeNull();
    });
  });
});
