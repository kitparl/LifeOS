import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { PreviewInfo } from '../models/document-preview.model';

interface DownloadToken {
  token: string;
  expires_at: string;
}

/**
 * Thin HTTP wrapper for the document-preview endpoints on the Files API.
 * Mirrors FilesService.tokenUrl — mints a short-lived download token so
 * <img>/<video>/<iframe>/PDF.js requests (which can't send an Authorization
 * header) can load preview/download bytes directly.
 */
@Injectable({ providedIn: 'root' })
export class DocumentPreviewApiService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/files`;
  private readonly apiRoot = environment.apiUrl.replace(/\/api\/v1$/, '');

  getPreviewInfo(documentId: string, opts?: { retry?: boolean }): Observable<PreviewInfo> {
    let params = new HttpParams();
    if (opts?.retry) params = params.set('retry', 'true');
    return this.http.get<PreviewInfo>(`${this.api}/${documentId}/preview-info`, { params });
  }

  private downloadToken(documentId: string): Observable<string> {
    return this.http
      .post<DownloadToken>(`${this.api}/${documentId}/download-token`, {})
      .pipe(map((t) => t.token));
  }

  /** Token URL for the renderable bytes — original or converted PDF. */
  previewUrl(documentId: string): Observable<string> {
    return this.downloadToken(documentId).pipe(
      map((token) => `${this.apiRoot}/api/v1/files/${documentId}/preview?token=${encodeURIComponent(token)}`),
    );
  }

  /** Token URL for the original file, always Content-Disposition: attachment. */
  downloadUrl(documentId: string): Observable<string> {
    return this.downloadToken(documentId).pipe(
      map((token) => `${this.apiRoot}/api/v1/files/${documentId}/download?token=${encodeURIComponent(token)}`),
    );
  }

  /** Raw text/CSV/JSON/XML content, authenticated via Bearer (renderers decode it themselves). */
  fetchText(documentId: string): Observable<string> {
    return this.http.get(`${this.api}/${documentId}/preview`, { responseType: 'text' });
  }
}
