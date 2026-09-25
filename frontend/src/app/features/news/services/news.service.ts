import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, shareReplay, throwError } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  NewsArticleDetail,
  NewsArticlePage,
  NewsCategory,
  NewsCollection,
  NewsQuery,
  SavedArticle,
  SavedArticleCreate,
  SavedArticlePage,
  SavedFilter,
} from '../models/news.models';

/** Live news is reused for this long while navigating, then refetched. Never persisted. */
export const NEWS_CACHE_TTL_MS = 2 * 60 * 1000;

interface CacheEntry<T> {
  at: number;
  value$: Observable<T>;
}

@Injectable({ providedIn: 'root' })
export class NewsService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/news`;
  private readonly cache = new Map<string, CacheEntry<unknown>>();

  /** Clock seam for tests. */
  now: () => number = () => Date.now();

  // ------------------------------------------------------------------ live news (cached)

  categories(): Observable<NewsCategory[]> {
    return this.cached('categories', () => this.http.get<NewsCategory[]>(`${this.api}/categories`));
  }

  articles(query: NewsQuery): Observable<NewsArticlePage> {
    const params = toParams(query);
    return this.cached(`articles?${params.toString()}`, () =>
      this.http.get<NewsArticlePage>(`${this.api}/articles`, { params }),
    );
  }

  article(url: string): Observable<NewsArticleDetail> {
    const params = new HttpParams().set('url', url);
    return this.cached(`article?${params.toString()}`, () =>
      this.http.get<NewsArticleDetail>(`${this.api}/article`, { params }),
    );
  }

  /** Drop cached live news (e.g. after saving, so saved stars stay accurate on return). */
  invalidateNews(): void {
    this.cache.clear();
  }

  // ------------------------------------------------------------------ saved articles

  listSaved(filter: SavedFilter, limit: number, offset: number): Observable<SavedArticlePage> {
    return this.http.get<SavedArticlePage>(`${this.api}/saved`, { params: { filter, limit, offset } });
  }

  save(article: SavedArticleCreate): Observable<SavedArticle> {
    return this.http.post<SavedArticle>(`${this.api}/saved`, article);
  }

  removeSaved(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/saved/${encodeURIComponent(id)}`);
  }

  // ------------------------------------------------------------------ collections

  listCollections(): Observable<NewsCollection[]> {
    return this.http.get<NewsCollection[]>(`${this.api}/collections`);
  }

  createCollection(name: string): Observable<NewsCollection> {
    return this.http.post<NewsCollection>(`${this.api}/collections`, { name });
  }

  renameCollection(id: string, name: string): Observable<NewsCollection> {
    return this.http.patch<NewsCollection>(this.collection(id), { name });
  }

  deleteCollection(id: string): Observable<void> {
    return this.http.delete<void>(this.collection(id));
  }

  listCollectionArticles(id: string, limit: number, offset: number): Observable<SavedArticlePage> {
    return this.http.get<SavedArticlePage>(`${this.collection(id)}/articles`, { params: { limit, offset } });
  }

  addToCollection(id: string, savedArticleId: string): Observable<SavedArticle> {
    return this.http.post<SavedArticle>(`${this.collection(id)}/articles`, { saved_article_id: savedArticleId });
  }

  removeFromCollection(id: string, savedArticleId: string): Observable<void> {
    return this.http.delete<void>(`${this.collection(id)}/articles/${encodeURIComponent(savedArticleId)}`);
  }

  moveToCollection(id: string, savedArticleId: string, targetId: string): Observable<SavedArticle> {
    return this.http.post<SavedArticle>(`${this.collection(id)}/articles/${encodeURIComponent(savedArticleId)}/move`, {
      target_collection_id: targetId,
    });
  }

  private collection(id: string): string {
    return `${this.api}/collections/${encodeURIComponent(id)}`;
  }

  /** Short-lived cache with in-flight dedup: concurrent subscribers share one request; errors are not kept. */
  private cached<T>(key: string, fetch: () => Observable<T>): Observable<T> {
    const hit = this.cache.get(key) as CacheEntry<T> | undefined;
    if (hit && this.now() - hit.at < NEWS_CACHE_TTL_MS) {
      return hit.value$;
    }
    const value$ = fetch().pipe(
      catchError((err: unknown) => {
        this.cache.delete(key);
        return throwError(() => err);
      }),
      shareReplay({ bufferSize: 1, refCount: false }),
    );
    this.cache.set(key, { at: this.now(), value$ });
    return value$;
  }
}

function toParams(query: NewsQuery): HttpParams {
  let params = new HttpParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== '') {
      params = params.set(key, String(value));
    }
  }
  return params;
}
