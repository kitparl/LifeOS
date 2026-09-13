import {
  KnowledgeChapter,
  KnowledgeSection,
  KnowledgeSubjectDetail,
} from './models/knowledge-notes.models';

export function isSectionComplete(chapter: KnowledgeChapter, sec: KnowledgeSection): boolean {
  return !!(chapter.closed_at || sec.closed_at);
}

export function isChapterComplete(chapter: KnowledgeChapter): boolean {
  if (chapter.closed_at) return true;
  return chapter.sections.length > 0 && chapter.sections.every((s) => !!s.closed_at);
}

export function resolveDefaultSection(
  subject: KnowledgeSubjectDetail,
  lastEditedSectionId: string | null,
): { section: KnowledgeSection; chapter: KnowledgeChapter } | null {
  const pairs: { section: KnowledgeSection; chapter: KnowledgeChapter }[] = [];
  for (const chapter of subject.chapters) {
    for (const section of chapter.sections) {
      pairs.push({ section, chapter });
    }
  }
  if (pairs.length === 0) return null;

  const incomplete = pairs.filter(({ section, chapter }) => !isSectionComplete(chapter, section));

  if (incomplete.length === 0) {
    return pairs[0];
  }

  if (lastEditedSectionId) {
    const lastEdited = incomplete.find(({ section }) => section.id === lastEditedSectionId);
    if (lastEdited) return lastEdited;
  }

  return incomplete[0];
}

export function stripFileMarkdown(content: string, fileId: string): string {
  if (!content || !fileId) return content;
  const escaped = fileId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp(`!?\\[[^\\]]*\\]\\([^)]*\\/files\\/${escaped}\\/content[^)]*\\)`, 'gi');
  return content.replace(re, '').replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trimEnd();
}
