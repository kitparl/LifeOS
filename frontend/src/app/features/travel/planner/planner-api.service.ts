import { HttpClient, HttpContext, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { SKIP_LIFEOS_AUTH } from '../../../core/utils/http';
import { GeoLookup, Suggestions } from '../models/travel.models';
import {
  JoinResult,
  MyPlan,
  MyView,
  PlanDocument,
  PublicPlanView,
  ResolvedLink,
  RoadRoute,
  ShareSession,
} from '../models/share.models';
import { LatLngBias } from '../utils/place-suggestions';

/** The owner is detected from a LifeOS sign-in on the first read only; nothing else carries the LifeOS session. */
const PUBLIC = { context: new HttpContext().set(SKIP_LIFEOS_AUTH, true) };

/** Calls of the public friend planner (`/travel/shared/<code>`). Friends act with `X-Share-Token`. */
@Injectable({ providedIn: 'root' })
export class PlannerApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/travel/shared`;

  private opts(token: string, revision?: number) {
    let headers = new HttpHeaders({ 'X-Share-Token': token });
    if (revision !== undefined) headers = headers.set('If-Match', `"${revision}"`);
    return { ...PUBLIC, headers };
  }

  /** Sends the LifeOS sign-in, if any, so the owner is recognised. */
  view(code: string): Observable<PublicPlanView> {
    return this.http.get<PublicPlanView>(`${this.base}/${code}`);
  }

  /** The same read without the LifeOS sign-in (an expired session must not block the plan). */
  viewAsGuest(code: string): Observable<PublicPlanView> {
    return this.http.get<PublicPlanView>(`${this.base}/${code}`, PUBLIC);
  }

  joinName(code: string, name: string): Observable<JoinResult> {
    return this.http.post<JoinResult>(`${this.base}/${code}/join/name`, { name }, PUBLIC);
  }

  joinGoogle(code: string, credential: string): Observable<JoinResult | { owner: true }> {
    return this.http.post<JoinResult | { owner: true }>(`${this.base}/${code}/join/google`, { credential }, PUBLIC);
  }

  renew(code: string, deviceSecret: string): Observable<ShareSession> {
    return this.http.post<ShareSession>(`${this.base}/${code}/session`, { device_secret: deviceSecret }, PUBLIC);
  }

  upgradeGoogle(code: string, token: string, credential: string): Observable<JoinResult> {
    return this.http.post<JoinResult>(`${this.base}/${code}/me/upgrade-google`, { credential }, this.opts(token));
  }

  me(code: string, token: string): Observable<MyView> {
    return this.http.get<MyView>(`${this.base}/${code}/me`, this.opts(token));
  }

  startPlan(code: string, token: string): Observable<MyPlan> {
    return this.http.post<MyPlan>(`${this.base}/${code}/me/plan`, {}, this.opts(token));
  }

  savePlan(code: string, token: string, revision: number, doc: PlanDocument): Observable<MyPlan> {
    return this.http.put<MyPlan>(`${this.base}/${code}/me/plan`, doc, this.opts(token, revision));
  }

  resetPlan(code: string, token: string, revision: number): Observable<MyPlan> {
    return this.http.post<MyPlan>(`${this.base}/${code}/me/plan/reset`, {}, this.opts(token, revision));
  }

  submit(code: string, token: string, message: string | null): Observable<MyPlan> {
    return this.http.post<MyPlan>(`${this.base}/${code}/me/plan/submit`, { message }, this.opts(token));
  }

  autocomplete(code: string, token: string, query: string, session: string, bias: LatLngBias): Observable<Suggestions> {
    let params = new HttpParams().set('q', query).set('session', session);
    if (bias) params = params.set('lat', bias.lat.toFixed(5)).set('lng', bias.lng.toFixed(5));
    return this.http.get<Suggestions>(`${this.base}/${code}/maps/autocomplete`, { ...this.opts(token), params });
  }

  placeDetails(code: string, token: string, placeId: string, session: string): Observable<GeoLookup> {
    const params = new HttpParams().set('session', session);
    return this.http.get<GeoLookup>(`${this.base}/${code}/maps/place/${encodeURIComponent(placeId)}`, { ...this.opts(token), params });
  }

  resolveLink(code: string, token: string, url: string): Observable<ResolvedLink> {
    return this.http.get<ResolvedLink>(`${this.base}/${code}/resolve-link`, { ...this.opts(token), params: { url } });
  }

  route(code: string, token: string, points: [number, number][]): Observable<RoadRoute> {
    return this.http.post<RoadRoute>(`${this.base}/${code}/route`, { points }, this.opts(token));
  }

  /** The plan the link shows (the final plan once locked) as the PDF guide. */
  shownPdf(code: string): Observable<Blob> {
    return this.http.get(`${this.base}/${code}/pdf`, { ...PUBLIC, responseType: 'blob' });
  }

  myPlanPdf(code: string, token: string): Observable<Blob> {
    return this.http.get(`${this.base}/${code}/me/plan/pdf`, { ...this.opts(token), responseType: 'blob' });
  }
}
