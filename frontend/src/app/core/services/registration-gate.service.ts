import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  RegistrationGateLoginRequest,
  RegistrationGateStatus,
} from '../models/auth.models';

@Injectable({ providedIn: 'root' })
export class RegistrationGateService {
  private readonly http = inject(HttpClient);

  login(data: RegistrationGateLoginRequest): Observable<void> {
    return this.http
      .post<{ ok: boolean }>(`${environment.apiUrl}/auth/registration-gate/login`, data, {
        withCredentials: true,
      })
      .pipe(map(() => undefined));
  }

  logout(): Observable<void> {
    return this.http
      .post<{ ok: boolean }>(`${environment.apiUrl}/auth/registration-gate/logout`, {}, {
        withCredentials: true,
      })
      .pipe(map(() => undefined));
  }

  status(): Observable<RegistrationGateStatus> {
    return this.http.get<RegistrationGateStatus>(
      `${environment.apiUrl}/auth/registration-gate/status`,
      { withCredentials: true },
    );
  }
}
