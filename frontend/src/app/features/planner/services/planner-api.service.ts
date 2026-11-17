import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { PlannerContent, PlannerNode, PlannerNodeKind } from '../models/planner.models';

export interface PlannerNodeCreate {
  parent_id: string | null;
  kind: PlannerNodeKind;
  name: string;
}

export interface PlannerNodeUpdate {
  name?: string;
  parent_id?: string | null;
  order_index?: number;
}

export interface PlannerContentSave {
  content: string;
  base_revision: number;
}

@Injectable({ providedIn: 'root' })
export class PlannerApiService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/planner/nodes`;

  list(): Observable<PlannerNode[]> {
    return this.http.get<PlannerNode[]>(this.api);
  }

  create(body: PlannerNodeCreate): Observable<PlannerNode> {
    return this.http.post<PlannerNode>(this.api, body);
  }

  update(id: string, body: PlannerNodeUpdate): Observable<PlannerNode> {
    return this.http.patch<PlannerNode>(`${this.api}/${id}`, body);
  }

  duplicate(id: string): Observable<PlannerNode> {
    return this.http.post<PlannerNode>(`${this.api}/${id}/duplicate`, {});
  }

  remove(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  getContent(id: string): Observable<PlannerContent> {
    return this.http.get<PlannerContent>(`${this.api}/${id}/content`);
  }

  saveContent(id: string, body: PlannerContentSave): Observable<PlannerContent> {
    return this.http.put<PlannerContent>(`${this.api}/${id}/content`, body);
  }
}
