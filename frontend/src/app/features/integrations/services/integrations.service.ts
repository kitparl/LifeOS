import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface IntegrationProvider {
  provider: string;
  display_name: string;
  description: string;
  oauth_required: boolean;
}

export interface IntegrationConnection {
  id: string;
  provider: string;
  display_name: string;
  enabled: boolean;
  status: string;
  last_sync_at: string | null;
}

export interface TelegramConfigStatus {
  connection_id: string;
  provider: string;
  enabled: boolean;
  status: string;
  configured: boolean;
  bot_token_masked: string | null;
  chat_id: string | null;
  last_sync_at: string | null;
  last_digest_at: string | null;
  notify_on: string[];
  digest_enabled: boolean;
  digest_time: string;
  digest_frequency: string;
  digest_weekday: number;
  timezone: string;
  morning_enabled: boolean;
  morning_time: string;
  midday_enabled: boolean;
  midday_time: string;
  night_enabled: boolean;
  night_time: string;
  weekly_enabled: boolean;
  weekly_time: string;
  weekly_weekday: number;
  ai_briefing_enabled: boolean;
  ai_briefing_time: string;
  birthday_reminders_enabled: boolean;
  immutable_reminders_enabled: boolean;
  routine_reminders_enabled: boolean;
  webhook_configured: boolean;
  webhook_url: string | null;
}

export interface TelegramConfigUpdate {
  bot_token?: string | null;
  chat_id?: string | null;
  enabled?: boolean | null;
  notify_on?: string[] | null;
  digest_enabled?: boolean | null;
  digest_time?: string | null;
  digest_frequency?: string | null;
  digest_weekday?: number | null;
  timezone?: string | null;
  morning_enabled?: boolean | null;
  morning_time?: string | null;
  midday_enabled?: boolean | null;
  midday_time?: string | null;
  night_enabled?: boolean | null;
  night_time?: string | null;
  weekly_enabled?: boolean | null;
  weekly_time?: string | null;
  weekly_weekday?: number | null;
  ai_briefing_enabled?: boolean | null;
  ai_briefing_time?: string | null;
  birthday_reminders_enabled?: boolean | null;
  immutable_reminders_enabled?: boolean | null;
  routine_reminders_enabled?: boolean | null;
}

export interface ReportRun {
  id: string;
  job_type: string;
  job_id: string;
  status: string;
  skip_reason: string | null;
  error: string | null;
  sections_json: string | null;
  dedupe_key: string | null;
  message_chars: number | null;
  scheduled_for: string | null;
  started_at: string;
  finished_at: string | null;
  created_at: string;
}

export interface TelegramTestResponse {
  ok: boolean;
  detail: string;
  bot_username: string | null;
}

export interface ChatCandidate {
  chat_id: string;
  type: string | null;
  title: string | null;
  username: string | null;
}

export interface DetectChatIdResponse {
  candidates: ChatCandidate[];
  detail: string;
}

export interface DigestResponse {
  sent: boolean;
  detail: string;
  sections: Record<string, number>;
}

export interface TelegramWebhookStatus {
  configured: boolean;
  url: string | null;
  pending_update_count: number | null;
  last_error_message: string | null;
  detail: string;
}

export interface TelegramWebhookRegisterResponse {
  ok: boolean;
  detail: string;
  webhook_url: string | null;
}

export const TELEGRAM_EVENT_OPTIONS: { key: string; label: string }[] = [
  { key: 'task_created', label: 'New task' },
  { key: 'race_added', label: 'New race' },
  { key: 'calendar_event_created', label: 'New calendar event' },
  { key: 'habit_created', label: 'New habit' },
  { key: 'goal_created', label: 'New goal' },
  { key: 'goal_milestone_added', label: 'Goal milestone' },
];

export type ReportJobType = 'morning' | 'midday' | 'night' | 'weekly' | 'ai_briefing';

@Injectable({ providedIn: 'root' })
export class IntegrationsService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/integrations`;

  providers(): Observable<IntegrationProvider[]> {
    return this.http.get<IntegrationProvider[]>(`${this.api}/providers`);
  }

  list(): Observable<IntegrationConnection[]> {
    return this.http.get<IntegrationConnection[]>(this.api);
  }

  connect(provider: string): Observable<IntegrationConnection> {
    return this.http.post<IntegrationConnection>(this.api, { provider, enabled: true });
  }

  toggle(id: string, enabled: boolean): Observable<IntegrationConnection> {
    return this.http.patch<IntegrationConnection>(`${this.api}/${id}`, { enabled });
  }

  sync(id: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.api}/${id}/sync`, {});
  }

  remove(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  getTelegram(): Observable<TelegramConfigStatus> {
    return this.http.get<TelegramConfigStatus>(`${this.api}/telegram`);
  }

  saveTelegramConfig(body: TelegramConfigUpdate): Observable<TelegramConfigStatus> {
    return this.http.put<TelegramConfigStatus>(`${this.api}/telegram/config`, body);
  }

  testConnection(connId: string): Observable<TelegramTestResponse> {
    return this.http.post<TelegramTestResponse>(`${this.api}/${connId}/test`, {});
  }

  detectChatId(connId: string, body?: { bot_token?: string }): Observable<DetectChatIdResponse> {
    return this.http.post<DetectChatIdResponse>(`${this.api}/${connId}/detect-chat-id`, body ?? {});
  }

  sendDigest(): Observable<DigestResponse> {
    return this.http.post<DigestResponse>(`${this.api}/telegram/digest`, {});
  }

  runReport(jobType: ReportJobType): Observable<DigestResponse> {
    return this.http.post<DigestResponse>(`${this.api}/telegram/reports/${jobType}/run`, {});
  }

  listReportRuns(limit = 20): Observable<ReportRun[]> {
    const params = new HttpParams().set('limit', String(limit));
    return this.http.get<ReportRun[]>(`${this.api}/telegram/report-runs`, { params });
  }

  getWebhookStatus(): Observable<TelegramWebhookStatus> {
    return this.http.get<TelegramWebhookStatus>(`${this.api}/telegram/webhook`);
  }

  registerWebhook(): Observable<TelegramWebhookRegisterResponse> {
    return this.http.post<TelegramWebhookRegisterResponse>(`${this.api}/telegram/webhook/register`, {});
  }

  deleteWebhook(): Observable<TelegramWebhookRegisterResponse> {
    return this.http.delete<TelegramWebhookRegisterResponse>(`${this.api}/telegram/webhook`);
  }
}
