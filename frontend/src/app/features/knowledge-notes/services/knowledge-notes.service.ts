import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ChapterCreate,
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

  // Search
  search(q: string): Observable<KnowledgeSearchHit[]> {
    const params = new HttpParams().set('q', q);
    return this.http.get<KnowledgeSearchHit[]>(`${this.api}/search`, { params });
  }
}
