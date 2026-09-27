import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  SplitBalances,
  SplitExpense,
  SplitExpensePayload,
  SplitGroupCreatePayload,
  SplitGroupView,
  SplitHistoryItem,
  SplitJoinPayload,
  SplitMember,
  SplitMemberUpdatePayload,
  SplitSeatIssued,
  SplitSettlement,
  SplitSettlementPayload,
} from '../models/split.models';

export const SPLIT_SEAT_HEADER = 'X-Split-Seat';

function seatHeaders(seatSecret: string | null | undefined): HttpHeaders {
  return seatSecret ? new HttpHeaders({ [SPLIT_SEAT_HEADER]: seatSecret }) : new HttpHeaders();
}

@Injectable({ providedIn: 'root' })
export class SplitsApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/splits`;

  createGroup(payload: SplitGroupCreatePayload): Observable<SplitSeatIssued> {
    return this.http.post<SplitSeatIssued>(`${this.base}/groups`, payload);
  }

  getGroup(code: string, seatSecret?: string | null): Observable<SplitGroupView> {
    return this.http.get<SplitGroupView>(`${this.base}/groups/${code}`, { headers: seatHeaders(seatSecret) });
  }

  joinGroup(code: string, payload: SplitJoinPayload): Observable<SplitSeatIssued> {
    return this.http.post<SplitSeatIssued>(`${this.base}/groups/${code}/join`, payload);
  }

  addExpense(code: string, seatSecret: string, payload: SplitExpensePayload): Observable<SplitExpense> {
    return this.http.post<SplitExpense>(`${this.base}/groups/${code}/expenses`, payload, {
      headers: seatHeaders(seatSecret),
    });
  }

  updateMe(code: string, seatSecret: string, payload: SplitMemberUpdatePayload): Observable<SplitMember> {
    return this.http.patch<SplitMember>(`${this.base}/groups/${code}/members/me`, payload, {
      headers: seatHeaders(seatSecret),
    });
  }

  getBalances(code: string): Observable<SplitBalances> {
    return this.http.get<SplitBalances>(`${this.base}/groups/${code}/balances`);
  }

  markPaid(code: string, seatSecret: string, payload: SplitSettlementPayload): Observable<SplitSettlement> {
    return this.http.post<SplitSettlement>(`${this.base}/groups/${code}/settlements`, payload, {
      headers: seatHeaders(seatSecret),
    });
  }

  confirmSettlement(settlementId: string, seatSecret: string): Observable<SplitSettlement> {
    return this.http.post<SplitSettlement>(`${this.base}/settlements/${settlementId}/confirm`, null, {
      headers: seatHeaders(seatSecret),
    });
  }

  endGroup(code: string, seatSecret: string): Observable<void> {
    return this.http.post<void>(`${this.base}/groups/${code}/end`, null, { headers: seatHeaders(seatSecret) });
  }

  keepInHistory(code: string, seatSecret: string): Observable<void> {
    return this.http.post<void>(`${this.base}/groups/${code}/keep`, null, { headers: seatHeaders(seatSecret) });
  }

  history(): Observable<SplitHistoryItem[]> {
    return this.http.get<SplitHistoryItem[]>(`${this.base}/history`);
  }
}
