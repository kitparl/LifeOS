import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { FileRecord } from '../models/file.models';

@Injectable({ providedIn: 'root' })
export class FilesService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/files`;

  list(): Observable<FileRecord[]> {
    return this.http.get<FileRecord[]>(this.api);
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

  contentUrl(record: FileRecord): string {
    if (record.url.startsWith('http')) return record.url;
    const apiRoot = environment.apiUrl.replace(/\/api\/v1$/, '');
    return `${apiRoot}${record.url}`;
  }
}
