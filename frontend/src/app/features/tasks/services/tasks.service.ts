import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { Task, TaskCreate, TaskListItem, TaskUpdate } from '../models/task.models';

@Injectable({ providedIn: 'root' })
export class TasksService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/tasks`;

  list(opts?: {
    status?: string;
    priority?: string;
    category?: string;
    due_today?: boolean;
    search?: string;
  }): Observable<TaskListItem[]> {
    let params = new HttpParams();
    if (opts?.status) params = params.set('status', opts.status);
    if (opts?.priority) params = params.set('priority', opts.priority);
    if (opts?.category) params = params.set('category', opts.category);
    if (opts?.due_today) params = params.set('due_today', 'true');
    if (opts?.search) params = params.set('search', opts.search);
    return this.http.get<TaskListItem[]>(this.api, { params });
  }

  get(id: string): Observable<Task> {
    return this.http.get<Task>(`${this.api}/${id}`);
  }

  create(data: TaskCreate): Observable<Task> {
    return this.http.post<Task>(this.api, data);
  }

  update(id: string, data: TaskUpdate): Observable<Task> {
    return this.http.patch<Task>(`${this.api}/${id}`, data);
  }

  complete(id: string): Observable<Task> {
    return this.http.post<Task>(`${this.api}/${id}/complete`, {});
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }
}
