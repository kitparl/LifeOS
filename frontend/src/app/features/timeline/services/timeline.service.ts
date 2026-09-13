import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface TimelineItem {
  module: string;
  entity_type: string;
  id: string;
  title: string;
  occurred_at: string;
  route: string;
}

@Injectable({ providedIn: 'root' })
export class TimelineService {
  private readonly http = inject(HttpClient);

  list(): Observable<TimelineItem[]> {
    return this.http.get<TimelineItem[]>(`${environment.apiUrl}/timeline`);
  }
}
