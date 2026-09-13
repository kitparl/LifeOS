import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface OcrDocument {
  id: string;
  file_id: string | null;
  filename: string;
  doc_type: string;
  extracted_text: string | null;
  status: string;
  created_at: string;
}

export interface OcrListResult {
  items: OcrDocument[];
  total: number;
}

@Injectable({ providedIn: 'root' })
export class OcrService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/ocr`;

  list(opts?: { limit?: number; offset?: number }): Observable<OcrListResult> {
    let params = new HttpParams();
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http.get<OcrDocument[]>(`${this.api}/documents`, { params, observe: 'response' }).pipe(
      map((response: HttpResponse<OcrDocument[]>) => ({
        items: response.body ?? [],
        total: Number(response.headers.get('X-Total-Count') ?? response.body?.length ?? 0),
      })),
    );
  }

  upload(file: File, docType: string): Observable<OcrDocument> {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('doc_type', docType);
    return this.http.post<OcrDocument>(`${this.api}/documents/upload`, fd);
  }

  createFromText(data: { filename: string; doc_type: string; text: string }): Observable<OcrDocument> {
    return this.http.post<OcrDocument>(`${this.api}/documents`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/documents/${id}`);
  }
}
