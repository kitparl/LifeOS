import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface LifeTimelineItem {
  item_type: string;
  module: string;
  id: string;
  title: string;
  description: string | null;
  occurred_at: string;
  route: string | null;
  photo_file_ids: string | null;
  ai_generated: boolean;
  tags: string | null;
}

export interface Milestone {
  id: string;
  title: string;
  description: string | null;
  milestone_date: string;
  tags: string | null;
  ai_generated: boolean;
}

@Injectable({ providedIn: 'root' })
export class LifeTimelineService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/life-timeline`;

  list(limit = 150): Observable<LifeTimelineItem[]> {
    return this.http.get<LifeTimelineItem[]>(this.api, { params: { limit } });
  }

  createMilestone(data: {
    title: string;
    description?: string;
    milestone_date: string;
    tags?: string;
  }): Observable<Milestone> {
    return this.http.post<Milestone>(`${this.api}/milestones`, data);
  }
}
