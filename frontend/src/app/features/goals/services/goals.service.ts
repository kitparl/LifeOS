import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  Goal,
  GoalCreate,
  GoalListItem,
  GoalUpdate,
  Milestone,
} from '../models/goal.models';

@Injectable({ providedIn: 'root' })
export class GoalsService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/goals`;

  list(category?: string, status?: string): Observable<GoalListItem[]> {
    let params = new HttpParams();
    if (category) params = params.set('category', category);
    if (status) params = params.set('status', status);
    return this.http.get<GoalListItem[]>(this.api, { params });
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
}
