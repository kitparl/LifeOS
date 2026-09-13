import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  Goal,
  GoalCreate,
  GoalListItem,
  GoalUpdate,
  Milestone,
} from '../models/goal.models';

export interface GoalListResult {
  items: GoalListItem[];
  total: number;
}

@Injectable({ providedIn: 'root' })
export class GoalsService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/goals`;

  list(opts?: {
    category?: string;
    status?: string;
    period?: string;
    missed?: boolean;
    limit?: number;
    offset?: number;
  }): Observable<GoalListResult> {
    let params = new HttpParams();
    if (opts?.category) params = params.set('category', opts.category);
    if (opts?.status) params = params.set('status', opts.status);
    if (opts?.period) params = params.set('period', opts.period);
    if (opts?.missed === true) params = params.set('missed', 'true');
    if (opts?.missed === false) params = params.set('missed', 'false');
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http.get<GoalListItem[]>(this.api, { params, observe: 'response' }).pipe(
      map((response: HttpResponse<GoalListItem[]>) => ({
        items: response.body ?? [],
        total: Number(response.headers.get('X-Total-Count') ?? response.body?.length ?? 0),
      })),
    );
  }

  get(id: string): Observable<Goal> {
    return this.http.get<Goal>(`${this.api}/${id}`);
  }

  create(data: GoalCreate): Observable<Goal> {
    return this.http.post<Goal>(this.api, data);
  }

  update(id: string, data: GoalUpdate): Observable<Goal> {
    return this.http.patch<Goal>(`${this.api}/${id}`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  archive(id: string): Observable<Goal> {
    return this.http.post<Goal>(`${this.api}/${id}/archive`, {});
  }

  addMilestone(goalId: string, title: string): Observable<Milestone> {
    return this.http.post<Milestone>(`${this.api}/${goalId}/milestones`, { title });
  }

  updateMilestone(goalId: string, milestoneId: string, data: { title?: string; completed?: boolean }): Observable<Milestone> {
    return this.http.patch<Milestone>(`${this.api}/${goalId}/milestones/${milestoneId}`, data);
  }

  deleteMilestone(goalId: string, milestoneId: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${goalId}/milestones/${milestoneId}`);
  }

  listCategories(): Observable<string[]> {
    return this.http.get<string[]>(`${this.api}/categories`);
  }

  createCategory(name: string): Observable<string[]> {
    return this.http.post<string[]>(`${this.api}/categories`, { name });
  }
}
