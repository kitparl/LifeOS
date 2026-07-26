import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ActivityLogEntry,
  StatusHistoryEntry,
  Task,
  TaskAssignment,
  TaskCreate,
  TaskListItem,
  TaskNote,
  TaskScope,
  TaskTag,
  TaskUpdate,
  TaskWatcher,
} from '../models/task.models';

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
    scope?: TaskScope;
    include_archived?: boolean;
    limit?: number;
    offset?: number;
  }): Observable<TaskListItem[]> {
    let params = new HttpParams();
    if (opts?.status) params = params.set('status', opts.status);
    if (opts?.priority) params = params.set('priority', opts.priority);
    if (opts?.category) params = params.set('category', opts.category);
    if (opts?.due_today) params = params.set('due_today', 'true');
    if (opts?.search) params = params.set('search', opts.search);
    if (opts?.scope) params = params.set('scope', opts.scope);
    if (opts?.include_archived) params = params.set('include_archived', 'true');
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
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

  archive(id: string): Observable<Task> {
    return this.http.post<Task>(`${this.api}/${id}/archive`, {});
  }

  restore(id: string): Observable<Task> {
    return this.http.post<Task>(`${this.api}/${id}/restore`, {});
  }

  assign(id: string, data: { assignee_username?: string; assignee_user_id?: string; reason?: string }): Observable<TaskAssignment> {
    return this.http.post<TaskAssignment>(`${this.api}/${id}/assign`, data);
  }

  cancelAssignment(taskId: string, assignmentId: string): Observable<TaskAssignment> {
    return this.http.post<TaskAssignment>(`${this.api}/${taskId}/assignments/${assignmentId}/cancel`, {});
  }

  acceptAssignment(taskId: string, assignmentId: string): Observable<TaskAssignment> {
    return this.http.post<TaskAssignment>(`${this.api}/${taskId}/assignments/${assignmentId}/accept`, {});
  }

  rejectAssignment(taskId: string, assignmentId: string, reason?: string): Observable<TaskAssignment> {
    return this.http.post<TaskAssignment>(`${this.api}/${taskId}/assignments/${assignmentId}/reject`, { reason });
  }

  listAssignments(taskId: string): Observable<TaskAssignment[]> {
    return this.http.get<TaskAssignment[]>(`${this.api}/${taskId}/assignments`);
  }

  activity(taskId: string): Observable<ActivityLogEntry[]> {
    return this.http.get<ActivityLogEntry[]>(`${this.api}/${taskId}/activity`);
  }

  statusHistory(taskId: string): Observable<StatusHistoryEntry[]> {
    return this.http.get<StatusHistoryEntry[]>(`${this.api}/${taskId}/status-history`);
  }

  listWatchers(taskId: string): Observable<TaskWatcher[]> {
    return this.http.get<TaskWatcher[]>(`${this.api}/${taskId}/watchers`);
  }

  addWatcher(taskId: string, data: { username?: string; user_id?: string }): Observable<TaskWatcher> {
    return this.http.post<TaskWatcher>(`${this.api}/${taskId}/watchers`, data);
  }

  removeWatcher(taskId: string, userId: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${taskId}/watchers/${userId}`);
  }

  listNotes(taskId: string): Observable<TaskNote[]> {
    return this.http.get<TaskNote[]>(`${this.api}/${taskId}/notes`);
  }

  addNote(taskId: string, body: string): Observable<TaskNote> {
    return this.http.post<TaskNote>(`${this.api}/${taskId}/notes`, { body });
  }

  deleteNote(taskId: string, noteId: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${taskId}/notes/${noteId}`);
  }

  listTags(taskId: string): Observable<TaskTag[]> {
    return this.http.get<TaskTag[]>(`${this.api}/${taskId}/tags`);
  }

  attachTag(taskId: string, name: string): Observable<TaskTag> {
    return this.http.post<TaskTag>(`${this.api}/${taskId}/tags`, { name });
  }

  detachTag(taskId: string, tagId: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${taskId}/tags/${tagId}`);
  }
}
