import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../../environments/environment';
import {
  BookmarkPage,
  BookmarkResponse,
  DailySetResponse,
  GameAnswerResponse,
  GameHistoryPage,
  GameSessionResponse,
  GameSource,
  GameType,
  GameVocabularyPage,
  HistoryPage,
  PersonalExample,
  SearchFilters,
  VocabularyDetailResponse,
  VocabularyPage,
  VocabularyProgress,
  VocabularySet,
} from '../models/vocabulary.models';

/**
 * Single source of backend vocabulary state. The frontend never decides which
 * vocabulary is next, whether midnight has passed, or whether a set is accepted —
 * every one of those is server-computed and returned here (PRD §35).
 */
@Injectable({ providedIn: 'root' })
export class VocabularyService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/communication/vocabulary`;

  // ---- Daily learning ---------------------------------------------------

  today(): Observable<DailySetResponse> {
    return this.http.get<DailySetResponse>(`${this.api}/today`);
  }

  accept(setId: string): Observable<VocabularySet> {
    return this.http.post<VocabularySet>(`${this.api}/sets/${setId}/accept`, {});
  }

  changeItem(setId: string, position: number): Observable<VocabularySet> {
    return this.http.post<VocabularySet>(`${this.api}/sets/${setId}/items/${position}/change`, {});
  }

  nextSet(): Observable<VocabularySet> {
    return this.http.post<VocabularySet>(`${this.api}/sets/next`, {});
  }

  // ---- Detail -------------------------------------------------------------

  getDetail(vocabularyId: string): Observable<VocabularyDetailResponse> {
    return this.http.get<VocabularyDetailResponse>(`${this.api}/${vocabularyId}`);
  }

  // ---- Bookmarks ------------------------------------------------------------

  addBookmark(vocabularyId: string): Observable<BookmarkResponse> {
    return this.http.post<BookmarkResponse>(`${this.api}/bookmarks/${vocabularyId}`, {});
  }

  removeBookmark(vocabularyId: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/bookmarks/${vocabularyId}`);
  }

  getBookmarks(limit = 25, offset = 0): Observable<BookmarkPage> {
    const params = new HttpParams().set('limit', limit).set('offset', offset);
    return this.http.get<BookmarkPage>(`${this.api}/bookmarks`, { params });
  }

  // ---- Personal examples ------------------------------------------------

  listExamples(vocabularyId: string): Observable<PersonalExample[]> {
    return this.http.get<PersonalExample[]>(`${this.api}/${vocabularyId}/examples`);
  }

  addExample(vocabularyId: string, sentence: string, notes?: string): Observable<PersonalExample> {
    return this.http.post<PersonalExample>(`${this.api}/${vocabularyId}/examples`, { sentence, notes });
  }

  updateExample(exampleId: string, sentence: string, notes?: string): Observable<PersonalExample> {
    return this.http.patch<PersonalExample>(`${this.api}/examples/${exampleId}`, { sentence, notes });
  }

  deleteExample(exampleId: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/examples/${exampleId}`);
  }

  // ---- History / Progress ------------------------------------------------

  getHistory(limit = 20, offset = 0): Observable<HistoryPage> {
    const params = new HttpParams().set('limit', limit).set('offset', offset);
    return this.http.get<HistoryPage>(`${this.api}/history`, { params });
  }

  getProgress(): Observable<VocabularyProgress> {
    return this.http.get<VocabularyProgress>(`${this.api}/progress`);
  }

  // ---- Search / Revision --------------------------------------------------

  search(filters: SearchFilters, limit = 20, offset = 0): Observable<VocabularyPage> {
    let params = new HttpParams().set('limit', limit).set('offset', offset);
    if (filters.q) params = params.set('q', filters.q);
    if (filters.level) params = params.set('level', filters.level);
    if (filters.type) params = params.set('type', filters.type);
    if (filters.topic) params = params.set('topic', filters.topic);
    return this.http.get<VocabularyPage>(`${this.api}/search`, { params });
  }

  getRevision(source: string, limit = 20, offset = 0): Observable<VocabularyPage> {
    const params = new HttpParams().set('source', source).set('limit', limit).set('offset', offset);
    return this.http.get<VocabularyPage>(`${this.api}/revision`, { params });
  }

  // ---- Games --------------------------------------------------------------

  getGameVocabulary(source: GameSource, level?: string, limit = 20): Observable<GameVocabularyPage> {
    let params = new HttpParams().set('source', source).set('limit', limit);
    if (level) params = params.set('level', level);
    return this.http.get<GameVocabularyPage>(`${this.api}/games/vocabulary`, { params });
  }

  createGameSession(gameType: GameType, source: GameSource, totalQuestions: number, level?: string): Observable<GameSessionResponse> {
    return this.http.post<GameSessionResponse>(`${this.api}/games/sessions`, {
      game_type: gameType,
      source,
      total_questions: totalQuestions,
      level,
    });
  }

  submitGameAnswer(
    sessionId: string,
    vocabularyId: string,
    questionType: GameType,
    isCorrect: boolean,
  ): Observable<GameAnswerResponse> {
    return this.http.post<GameAnswerResponse>(`${this.api}/games/sessions/${sessionId}/answers`, {
      vocabulary_id: vocabularyId,
      question_type: questionType,
      is_correct: isCorrect,
    });
  }

  completeGameSession(sessionId: string): Observable<GameSessionResponse> {
    return this.http.post<GameSessionResponse>(`${this.api}/games/sessions/${sessionId}/complete`, {});
  }

  getGameHistory(limit = 20, offset = 0): Observable<GameHistoryPage> {
    const params = new HttpParams().set('limit', limit).set('offset', offset);
    return this.http.get<GameHistoryPage>(`${this.api}/games/history`, { params });
  }
}
