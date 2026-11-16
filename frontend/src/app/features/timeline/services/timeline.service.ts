import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { TimelineItem, TimelineSource, TimelineSourceKey } from '../models/timeline.models';

@Injectable({ providedIn: 'root' })
export class TimelineService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/timeline`;

  sources(): Observable<TimelineSource[]> {
    return this.http.get<TimelineSource[]>(`${this.api}/sources`);
  }

  /** `start`/`end` are inclusive local `YYYY-MM-DD` dates. */
  list(start: string, end: string, sources: TimelineSourceKey[]): Observable<TimelineItem[]> {
    let params = new HttpParams().set('start', start).set('end', end);
    for (const s of sources) params = params.append('sources', s);
    return this.http.get<TimelineItem[]>(this.api, { params });
  }
}
