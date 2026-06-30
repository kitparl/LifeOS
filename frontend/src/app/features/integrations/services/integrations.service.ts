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
}
