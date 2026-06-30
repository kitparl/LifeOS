import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ExportService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/export`;

  listModules(): Observable<{ modules: string[]; formats: string[] }> {
    return this.http.get<{ modules: string[]; formats: string[] }>(`${this.api}/modules`);
  }

  download(module: string, format: 'json' | 'csv'): Observable<Blob> {
    const params = new HttpParams().set('format', format);
    return this.http.get(`${this.api}/${module}`, { params, responseType: 'blob' });
  }
}
