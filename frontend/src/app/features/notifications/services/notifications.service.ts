import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { Notification, NotificationSettings } from '../models/notification.models';
import { Page, toPage } from '../../../core/utils/http';

export type NotificationListResult = Page<Notification>;

@Injectable({ providedIn: 'root' })
export class NotificationsService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/notifications`;

  list(opts?: {
    unreadOnly?: boolean;
    limit?: number;
    offset?: number;
  }): Observable<NotificationListResult> {
    let params = new HttpParams()
      .set('unread_only', String(opts?.unreadOnly ?? false))
      .set('limit', String(opts?.limit ?? 25));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return this.http.get<Notification[]>(this.api, { params, observe: 'response' }).pipe(
      map(toPage),
    );
  }

  create(data: { message: string; route?: string | null; module?: string | null }): Observable<Notification> {
    return this.http.post<Notification>(this.api, data);
  }

  markRead(id: string): Observable<Notification> {
    return this.http.patch<Notification>(`${this.api}/${id}/read`, {});
  }

  markAllRead(): Observable<void> {
    return this.http.post<void>(`${this.api}/mark-all-read`, {});
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  getSettings(): Observable<NotificationSettings> {
    return this.http.get<NotificationSettings>(`${this.api}/settings`);
  }

  updateSettings(data: Partial<NotificationSettings>): Observable<NotificationSettings> {
    return this.http.patch<NotificationSettings>(`${this.api}/settings`, data);
  }

  sendTelegram(id: string): Observable<{ sent: boolean; detail: string }> {
    return this.http.post<{ sent: boolean; detail: string }>(`${this.api}/${id}/telegram`, {});
  }
}
