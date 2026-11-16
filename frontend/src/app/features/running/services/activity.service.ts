import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { toPage } from '../../../core/utils/http';
import {
  ActivityDetail,
  ActivitySeries,
  DeleteImportedResult,
  ImportJob,
  ImportRange,
  ImportedSummary,
} from '../models/activity.models';

@Injectable({ providedIn: 'root' })
export class ActivityService {
  private readonly http = inject(HttpClient);
  private readonly importsApi = `${environment.apiUrl}/integrations/garmin`;
  private readonly activitiesApi = `${environment.apiUrl}/activities`;

  startImport(files: File[], range: ImportRange): Observable<ImportJob> {
    const form = new FormData();
    for (const file of files) form.append('files', file, file.name);
    form.append('range', range);
    return this.http.post<ImportJob>(`${this.importsApi}/imports`, form);
  }

  getImport(id: string): Observable<ImportJob> {
    return this.http.get<ImportJob>(`${this.importsApi}/imports/${id}`);
  }

  listImports(opts?: { limit?: number; offset?: number }): Observable<{ items: ImportJob[]; total: number }> {
    let params = new HttpParams();
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http
      .get<ImportJob[]>(`${this.importsApi}/imports`, { params, observe: 'response' })
      .pipe(map(toPage));
  }

  getImportedSummary(): Observable<ImportedSummary> {
    return this.http.get<ImportedSummary>(`${this.importsApi}/data/summary`);
  }

  deleteImportedData(includeHealth = false): Observable<DeleteImportedResult> {
    const params = new HttpParams().set('include_health', String(includeHealth));
    return this.http.delete<DeleteImportedResult>(`${this.importsApi}/data`, { params });
  }

  getActivity(id: string): Observable<ActivityDetail> {
    return this.http.get<ActivityDetail>(`${this.activitiesApi}/${id}`);
  }

  getActivitySeries(id: string): Observable<ActivitySeries> {
    return this.http.get<ActivitySeries>(`${this.activitiesApi}/${id}/series`);
  }
}
