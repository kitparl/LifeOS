import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ApplyResult,
  LockResult,
  ShareSettingsUpdate,
  TripShare,
  VersionDetail,
  VersionRow,
} from '../models/share.models';

/** The owner's side of a shared trip plan: link, settings, versions, lock and apply. */
@Injectable({ providedIn: 'root' })
export class ShareApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/travel/trips`;

  private url(tripId: string, suffix = ''): string {
    return `${this.base}/${tripId}/share${suffix}`;
  }

  get(tripId: string): Observable<TripShare> {
    return this.http.get<TripShare>(this.url(tripId));
  }

  create(tripId: string): Observable<TripShare> {
    return this.http.post<TripShare>(this.url(tripId), {});
  }

  updateSettings(tripId: string, data: ShareSettingsUpdate): Observable<TripShare> {
    return this.http.patch<TripShare>(this.url(tripId, '/settings'), data);
  }

  revoke(tripId: string): Observable<TripShare> {
    return this.http.post<TripShare>(this.url(tripId, '/revoke'), {});
  }

  newLink(tripId: string): Observable<TripShare> {
    return this.http.post<TripShare>(this.url(tripId, '/new-link'), {});
  }

  lock(tripId: string, versionId: string, apply: boolean): Observable<LockResult> {
    return this.http.post<LockResult>(this.url(tripId, '/lock'), { version_id: versionId, apply });
  }

  unlock(tripId: string): Observable<TripShare> {
    return this.http.post<TripShare>(this.url(tripId, '/unlock'), {});
  }

  versions(tripId: string): Observable<VersionRow[]> {
    return this.http.get<VersionRow[]>(this.url(tripId, '/versions'));
  }

  version(tripId: string, versionId: string): Observable<VersionDetail> {
    return this.http.get<VersionDetail>(this.url(tripId, `/versions/${versionId}`));
  }

  snapshotTrip(tripId: string): Observable<VersionRow> {
    return this.http.post<VersionRow>(this.url(tripId, '/versions'), {});
  }

  rename(tripId: string, versionId: string, label: string): Observable<VersionRow> {
    return this.http.patch<VersionRow>(this.url(tripId, `/versions/${versionId}`), { label });
  }

  deleteVersion(tripId: string, versionId: string): Observable<void> {
    return this.http.delete<void>(this.url(tripId, `/versions/${versionId}`));
  }

  apply(tripId: string, versionId: string): Observable<ApplyResult> {
    return this.http.post<ApplyResult>(this.url(tripId, `/versions/${versionId}/apply`), {});
  }

  versionPdf(tripId: string, versionId: string): Observable<Blob> {
    return this.http.get(this.url(tripId, `/versions/${versionId}/export`), { responseType: 'blob' });
  }

  removeContributor(tripId: string, contributorId: string): Observable<TripShare> {
    return this.http.delete<TripShare>(this.url(tripId, `/contributors/${contributorId}`));
  }
}
