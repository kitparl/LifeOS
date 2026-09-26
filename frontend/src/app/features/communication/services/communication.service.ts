import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { SpeakingPractice, WritingEvaluation, WritingPractice, WritingRewrite } from '../models/communication.models';
import { Page, toPage } from '../../../core/utils/http';

export type CommunicationListResult<T> = Page<T>;

@Injectable({ providedIn: 'root' })
export class CommunicationService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/communication`;

  listWriting(opts?: {
    category?: string;
    limit?: number;
    offset?: number;
  }): Observable<CommunicationListResult<WritingPractice>> {
    let params = new HttpParams();
    if (opts?.category) params = params.set('category', opts.category);
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http.get<WritingPractice[]>(`${this.api}/writing`, { params, observe: 'response' }).pipe(
      map(toPage),
    );
  }

  getWriting(id: string): Observable<WritingPractice> {
    return this.http.get<WritingPractice>(`${this.api}/writing/${id}`);
  }

  createWriting(data: { title: string; content?: string; category?: string }): Observable<WritingPractice> {
    return this.http.post<WritingPractice>(`${this.api}/writing`, data);
  }

  listWritingCategories(): Observable<string[]> {
    return this.http.get<string[]>(`${this.api}/writing/categories`);
  }

  createWritingCategory(name: string): Observable<string[]> {
    return this.http.post<string[]>(`${this.api}/writing/categories`, { name });
  }

  updateWriting(id: string, data: Partial<WritingPractice>): Observable<WritingPractice> {
    return this.http.patch<WritingPractice>(`${this.api}/writing/${id}`, data);
  }

  deleteWriting(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/writing/${id}`);
  }

  requestAiFeedback(writingId: string): Observable<WritingEvaluation> {
    return this.http.post<WritingEvaluation>(`${this.api}/writing/${writingId}/ai-feedback`, {});
  }

  getAiFeedback(writingId: string): Observable<WritingEvaluation> {
    return this.http.get<WritingEvaluation>(`${this.api}/writing/${writingId}/ai-feedback`);
  }

  requestAiRewrite(writingId: string): Observable<WritingRewrite> {
    return this.http.post<WritingRewrite>(`${this.api}/writing/${writingId}/ai-rewrite`, {});
  }

  getAiRewrite(writingId: string): Observable<WritingRewrite> {
    return this.http.get<WritingRewrite>(`${this.api}/writing/${writingId}/ai-rewrite`);
  }

  listSpeaking(opts?: {
    category?: string;
    limit?: number;
    offset?: number;
  }): Observable<CommunicationListResult<SpeakingPractice>> {
    let params = new HttpParams();
    if (opts?.category) params = params.set('category', opts.category);
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http.get<SpeakingPractice[]>(`${this.api}/speaking`, { params, observe: 'response' }).pipe(
      map(toPage),
    );
  }

  getSpeaking(id: string): Observable<SpeakingPractice> {
    return this.http.get<SpeakingPractice>(`${this.api}/speaking/${id}`);
  }

  createSpeaking(data: {
    title: string;
    prompt: string;
    response?: string | null;
    category?: string;
    notes?: string | null;
  }): Observable<SpeakingPractice> {
    return this.http.post<SpeakingPractice>(`${this.api}/speaking`, data);
  }

  updateSpeaking(id: string, data: Partial<SpeakingPractice>): Observable<SpeakingPractice> {
    return this.http.patch<SpeakingPractice>(`${this.api}/speaking/${id}`, data);
  }

  deleteSpeaking(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/speaking/${id}`);
  }
}
