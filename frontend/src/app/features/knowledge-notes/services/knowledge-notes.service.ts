import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  isExecutableLanguage,
  parseFencedCodeBlocks,
} from '../../../shared/code-workspace/utils/fenced-code-blocks';
import {
  ChapterCreate,
  CodeBlock,
  KnowledgeChapter,
  KnowledgeSearchHit,
  KnowledgeSection,
  KnowledgeSubjectDetail,
  KnowledgeSubjectListItem,
  SectionCreate,
  SectionUpdate,
  SubjectCreate,
  SubjectUpdate,
} from '../models/knowledge-notes.models';

@Injectable({ providedIn: 'root' })
export class KnowledgeNotesService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/knowledge-notes`;
  private readonly codeBlockCache = new Map<string, CodeBlock[]>();

  // Subjects
  listSubjects(): Observable<KnowledgeSubjectListItem[]> {
    return this.http.get<KnowledgeSubjectListItem[]>(`${this.api}/subjects`);
  }

  getSubject(id: string): Observable<KnowledgeSubjectDetail> {
    return this.http.get<KnowledgeSubjectDetail>(`${this.api}/subjects/${id}`);
  }

  createSubject(data: SubjectCreate): Observable<KnowledgeSubjectDetail> {
    return this.http.post<KnowledgeSubjectDetail>(`${this.api}/subjects`, data);
  }

  updateSubject(id: string, data: SubjectUpdate): Observable<KnowledgeSubjectDetail> {
    return this.http.patch<KnowledgeSubjectDetail>(`${this.api}/subjects/${id}`, data);
  }

  deleteSubject(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/subjects/${id}`);
  }

  // Chapters
  createChapter(subjectId: string, data: ChapterCreate): Observable<KnowledgeChapter> {
    return this.http.post<KnowledgeChapter>(`${this.api}/subjects/${subjectId}/chapters`, data);
  }

  updateChapter(id: string, data: { title?: string; order_index?: number }): Observable<KnowledgeChapter> {
    return this.http.patch<KnowledgeChapter>(`${this.api}/chapters/${id}`, data);
  }

  deleteChapter(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/chapters/${id}`);
  }

  // Sections
  getSection(id: string): Observable<KnowledgeSection> {
    return this.http.get<KnowledgeSection>(`${this.api}/sections/${id}`);
  }

  createSection(chapterId: string, data: SectionCreate): Observable<KnowledgeSection> {
    return this.http.post<KnowledgeSection>(`${this.api}/chapters/${chapterId}/sections`, data);
  }

  updateSection(id: string, data: SectionUpdate): Observable<KnowledgeSection> {
    return this.http.patch<KnowledgeSection>(`${this.api}/sections/${id}`, data);
  }

  deleteSection(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/sections/${id}`);
  }

  archiveSection(id: string): Observable<KnowledgeSection> {
    return this.http.post<KnowledgeSection>(`${this.api}/sections/${id}/archive`, {});
  }

  restoreSection(id: string): Observable<KnowledgeSection> {
    return this.http.post<KnowledgeSection>(`${this.api}/sections/${id}/restore`, {});
  }

  // Search
  search(q: string): Observable<KnowledgeSearchHit[]> {
    const params = new HttpParams().set('q', q);
    return this.http.get<KnowledgeSearchHit[]>(`${this.api}/search`, { params });
  }

  parseCodeBlocks(markdown: string): CodeBlock[] {
    const cached = this.codeBlockCache.get(markdown);
    if (cached) {
      return cached;
    }
    const blocks = parseFencedCodeBlocks(markdown);
    this.codeBlockCache.set(markdown, blocks);
    if (this.codeBlockCache.size > 50) {
      const oldest = this.codeBlockCache.keys().next().value;
      if (oldest !== undefined) {
        this.codeBlockCache.delete(oldest);
      }
    }
    return blocks;
  }

  hasExecutableCode(section: KnowledgeSection): boolean {
    const blocks = section.codeBlocks ?? this.parseCodeBlocks(section.content || '');
    return blocks.some((block) => isExecutableLanguage(block.language));
  }

  enrichSection(section: KnowledgeSection): KnowledgeSection {
    const codeBlocks = this.parseCodeBlocks(section.content || '');
    const wordCount = section.content?.trim()
      ? section.content.trim().split(/\s+/).length
      : 0;
    return {
      ...section,
      format: 'markdown',
      codeBlocks,
      metadata: {
        lastModified: new Date(section.updated_at),
        wordCount,
        hasExecutableCode: codeBlocks.some((block) => isExecutableLanguage(block.language)),
      },
    };
  }

  async loadSection(sectionId: string): Promise<KnowledgeSection> {
    const section = await firstValueFrom(this.getSection(sectionId));
    return this.enrichSection(section);
  }

  async saveSection(section: KnowledgeSection): Promise<void> {
    await firstValueFrom(
      this.updateSection(section.id, {
        title: section.title,
        content: section.content,
      })
    );
  }
}
