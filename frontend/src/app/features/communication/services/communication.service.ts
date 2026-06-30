import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { SpeakingPractice, VocabularyWord, WritingPractice } from '../models/communication.models';

@Injectable({ providedIn: 'root' })
export class CommunicationService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/communication`;

  listVocabulary(search?: string): Observable<VocabularyWord[]> {
    let params = new HttpParams();
    if (search) params = params.set('search', search);
    return this.http.get<VocabularyWord[]>(`${this.api}/vocabulary`, { params });
  }

  getVocabulary(id: string): Observable<VocabularyWord> {
    return this.http.get<VocabularyWord>(`${this.api}/vocabulary/${id}`);
  }

  createVocabulary(data: Partial<VocabularyWord>): Observable<VocabularyWord> {
    return this.http.post<VocabularyWord>(`${this.api}/vocabulary`, data);
  }

  updateVocabulary(id: string, data: Partial<VocabularyWord>): Observable<VocabularyWord> {
    return this.http.patch<VocabularyWord>(`${this.api}/vocabulary/${id}`, data);
  }

  deleteVocabulary(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/vocabulary/${id}`);
  }

  listWriting(category?: string): Observable<WritingPractice[]> {
    let params = new HttpParams();
    if (category) params = params.set('category', category);
    return this.http.get<WritingPractice[]>(`${this.api}/writing`, { params });
  }

  getWriting(id: string): Observable<WritingPractice> {
    return this.http.get<WritingPractice>(`${this.api}/writing/${id}`);
  }

  createWriting(data: { title: string; content?: string; category?: string }): Observable<WritingPractice> {
    return this.http.post<WritingPractice>(`${this.api}/writing`, data);
  }

  updateWriting(id: string, data: Partial<WritingPractice>): Observable<WritingPractice> {
    return this.http.patch<WritingPractice>(`${this.api}/writing/${id}`, data);
  }

  deleteWriting(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/writing/${id}`);
  }

  listSpeaking(category?: string): Observable<SpeakingPractice[]> {
    let params = new HttpParams();
    if (category) params = params.set('category', category);
    return this.http.get<SpeakingPractice[]>(`${this.api}/speaking`, { params });
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
