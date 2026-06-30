import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
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

@Injectable({ providedIn: 'root' })
export class OcrService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/ocr`;

  list(): Observable<OcrDocument[]> {
    return this.http.get<OcrDocument[]>(`${this.api}/documents`);
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
