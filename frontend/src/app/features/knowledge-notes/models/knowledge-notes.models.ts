export interface KnowledgeExecutionResult {
  output: string;
  error: string | null;
  executionTime: number;
  timestamp: Date;
}

export interface CodeBlock {
  id: string;
  language: string;
  code: string;
  lineStart: number;
  lineEnd: number;
  executionResult?: KnowledgeExecutionResult;
}

export interface KnowledgeSectionMetadata {
  lastModified: Date;
  wordCount: number;
  hasExecutableCode: boolean;
}

export interface KnowledgeSection {
  id: string;
  chapter_id: string;
  title: string;
  content: string;
  order_index: number;
  created_at: string;
  updated_at: string;
  /** Client-only during HTML → Markdown transition. */
  format?: 'markdown' | 'html';
  /** Client-only parsed fences; not persisted separately. */
  codeBlocks?: CodeBlock[];
  metadata?: KnowledgeSectionMetadata;
}

export interface KnowledgeChapter {
  id: string;
  subject_id: string;
  title: string;
  order_index: number;
  sections: KnowledgeSection[];
}

export interface KnowledgeSubjectListItem {
  id: string;
  title: string;
  description: string | null;
  icon: string | null;
  order_index: number;
  chapter_count: number;
  section_count: number;
  updated_at: string;
}

export interface KnowledgeSubjectDetail {
  id: string;
  title: string;
  description: string | null;
  icon: string | null;
  order_index: number;
  created_at: string;
  updated_at: string;
  chapters: KnowledgeChapter[];
}

export interface KnowledgeSearchHit {
  section_id: string;
  section_title: string;
  chapter_id: string;
  chapter_title: string;
  subject_id: string;
  subject_title: string;
  snippet: string;
}

export interface SubjectCreate {
  title: string;
  description?: string | null;
  icon?: string | null;
}

export interface SubjectUpdate {
  title?: string;
  description?: string | null;
  icon?: string | null;
  order_index?: number;
}

export interface ChapterCreate {
  title: string;
  order_index?: number;
}

export interface SectionCreate {
  title: string;
  content?: string;
  order_index?: number;
}

export interface SectionUpdate {
  title?: string;
  content?: string;
  order_index?: number;
  chapter_id?: string;
}
