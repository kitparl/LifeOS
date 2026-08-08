import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ConceptNote,
  ConceptNoteCreate,
  ConceptUpdate,
  LearningConcept,
  LearningItem,
  LearningListItem,
  LearningResource,
  LearningTrack,
  SessionCreate,
  SessionStats,
  StudySession,
  TrackProgress,
} from '../models/learning.models';

@Injectable({ providedIn: 'root' })
export class LearningService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/learning`;
  private readonly api = `${this.base}/items`;

  list(itemType?: string): Observable<LearningListItem[]> {
    let params = new HttpParams();
    if (itemType) params = params.set('item_type', itemType);
    return this.http.get<LearningListItem[]>(this.api, { params });
  }

  get(id: string): Observable<LearningItem> {
    return this.http.get<LearningItem>(`${this.api}/${id}`);
  }

  create(data: Partial<LearningItem>): Observable<LearningItem> {
    return this.http.post<LearningItem>(this.api, data);
  }

  update(id: string, data: Partial<LearningItem>): Observable<LearningItem> {
    return this.http.patch<LearningItem>(`${this.api}/${id}`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  listTracks(): Observable<LearningTrack[]> {
    return this.http.get<LearningTrack[]>(`${this.base}/tracks`);
  }

  getTrack(id: string): Observable<LearningTrack> {
    return this.http.get<LearningTrack>(`${this.base}/tracks/${id}`);
  }

  seedTrack(slug: string): Observable<LearningTrack> {
    return this.http.post<LearningTrack>(`${this.base}/tracks/seed`, { slug });
  }

  getTrackProgress(id: string): Observable<TrackProgress> {
    return this.http.get<TrackProgress>(`${this.base}/tracks/${id}/progress`);
  }

  listConcepts(itemId?: string, week?: number): Observable<LearningConcept[]> {
    let params = new HttpParams();
    if (itemId) params = params.set('item_id', itemId);
    if (week != null) params = params.set('week', String(week));
    return this.http.get<LearningConcept[]>(`${this.base}/concepts`, { params });
  }

  getConcept(id: string): Observable<LearningConcept> {
    return this.http.get<LearningConcept>(`${this.base}/concepts/${id}`);
  }

  updateConcept(id: string, data: ConceptUpdate): Observable<LearningConcept> {
    return this.http.patch<LearningConcept>(`${this.base}/concepts/${id}`, data);
  }

  listResources(conceptId?: string, itemId?: string): Observable<LearningResource[]> {
    let params = new HttpParams();
    if (conceptId) params = params.set('concept_id', conceptId);
    if (itemId) params = params.set('item_id', itemId);
    return this.http.get<LearningResource[]>(`${this.base}/resources`, { params });
  }

  listConceptNotes(conceptId: string): Observable<ConceptNote[]> {
    return this.http.get<ConceptNote[]>(`${this.base}/concepts/${conceptId}/notes`);
  }

  attachConceptNote(conceptId: string, data: ConceptNoteCreate): Observable<ConceptNote> {
    return this.http.post<ConceptNote>(`${this.base}/concepts/${conceptId}/notes`, data);
  }

  detachConceptNote(conceptId: string, noteId: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/concepts/${conceptId}/notes/${noteId}`);
  }

  updateResource(id: string, data: { is_consumed?: boolean; notes?: string }): Observable<LearningResource> {
    return this.http.patch<LearningResource>(`${this.base}/resources/${id}`, data);
  }

  listSessions(from?: string, to?: string): Observable<StudySession[]> {
    let params = new HttpParams();
    if (from) params = params.set('from', from);
    if (to) params = params.set('to', to);
    return this.http.get<StudySession[]>(`${this.base}/sessions`, { params });
  }

  createSession(data: SessionCreate): Observable<StudySession> {
    return this.http.post<StudySession>(`${this.base}/sessions`, data);
  }

  sessionStats(): Observable<SessionStats> {
    return this.http.get<SessionStats>(`${this.base}/sessions/stats`);
  }
}
