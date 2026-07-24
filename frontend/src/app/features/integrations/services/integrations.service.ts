import { HttpClient } from '@angular/common/http';
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

  saveTelegramConfig(body: {
    bot_token?: string | null;
    chat_id?: string | null;
    enabled?: boolean | null;
  }): Observable<TelegramConfigStatus> {
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
}
