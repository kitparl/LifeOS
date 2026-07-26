import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { DownloadToken, FileRecord, FileUsage } from '../models/file.models';

@Injectable({ providedIn: 'root' })
export class FilesService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/files`;

  list(module?: string, entityId?: string): Observable<FileRecord[]> {
    let params = new HttpParams();
    if (module) params = params.set('module', module);
    if (entityId) params = params.set('entity_id', entityId);
    return this.http.get<FileRecord[]>(this.api, { params });
  }

  get(id: string): Observable<FileRecord> {
    return this.http.get<FileRecord>(`${this.api}/${id}`);
  }

  upload(file: File, module?: string, entityId?: string): Observable<FileRecord> {
    const form = new FormData();
    form.append('file', file);
    if (module) form.append('module', module);
    if (entityId) form.append('entity_id', entityId);
    return this.http.post<FileRecord>(`${this.api}/upload`, form);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  downloadToken(id: string): Observable<DownloadToken> {
    return this.http.post<DownloadToken>(`${this.api}/${id}/download-token`, {});
  }

  /** Mint a short-lived token URL suitable for <a href>, <img src>, iframe. */
  tokenUrl(id: string): Observable<string> {
    return this.downloadToken(id).pipe(
      map((t) => {
        const apiRoot = environment.apiUrl.replace(/\/api\/v1$/, '');
        return `${apiRoot}/api/v1/files/${id}/content?token=${encodeURIComponent(t.token)}`;
      }),
    );
  }

  /** Explicit download via authenticated blob request. */
  downloadBlob(id: string): Observable<Blob> {
    return this.http.get(`${this.api}/${id}/content`, { responseType: 'blob' });
  }

  setVisibility(id: string, visibility: 'private' | 'public'): Observable<FileRecord> {
    return this.http.patch<FileRecord>(`${this.api}/${id}`, { visibility });
  }

  usage(): Observable<FileUsage> {
    return this.http.get<FileUsage>(`${this.api}/usage`);
  }

  /** Legacy absolute/relative URL helper (wishlist FileUploadComponent). Prefer tokenUrl for browser opens. */
  contentUrl(record: FileRecord): string {
    if (record.url.startsWith('http')) return record.url;
    const apiRoot = environment.apiUrl.replace(/\/api\/v1$/, '');
    return `${apiRoot}${record.url}`;
  }

  openInNewTab(id: string): void {
    this.tokenUrl(id).subscribe({
      next: (url) => window.open(url, '_blank', 'noopener'),
    });
  }

  saveAsDownload(record: FileRecord): void {
    this.downloadBlob(record.id).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = record.filename;
        a.click();
        URL.revokeObjectURL(url);
      },
    });
  }
}
