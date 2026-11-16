import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  HealthDay,
  HealthRange,
  HealthToday,
  Measurement,
  MeasurementCreate,
  MeasurementKind,
  MetricInfo,
  MetricSeries,
  SleepResponse,
} from '../models/health.models';

@Injectable({ providedIn: 'root' })
export class HealthService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/health`;

  getCatalogue(): Observable<MetricInfo[]> {
    return this.http.get<MetricInfo[]>(`${this.api}/metrics`);
  }

  getToday(): Observable<HealthToday> {
    return this.http.get<HealthToday>(`${this.api}/today`);
  }

  getMetricSeries(key: string, range: HealthRange): Observable<MetricSeries> {
    return this.http.get<MetricSeries>(`${this.api}/metrics/${key}`, { params: { range } });
  }

  getSleep(range: HealthRange): Observable<SleepResponse> {
    return this.http.get<SleepResponse>(`${this.api}/sleep`, { params: { range } });
  }

  getDay(day: string): Observable<HealthDay> {
    return this.http.get<HealthDay>(`${this.api}/days/${day}`);
  }

  saveDay(day: string, values: Record<string, number>): Observable<HealthDay> {
    return this.http.put<HealthDay>(`${this.api}/days/${day}`, { values });
  }

  listMeasurements(kind: MeasurementKind, start: string, end: string): Observable<Measurement[]> {
    const params = new HttpParams().set('kind', kind).set('start', start).set('end', end);
    return this.http.get<Measurement[]>(`${this.api}/measurements`, { params });
  }

  addMeasurement(data: MeasurementCreate): Observable<Measurement> {
    return this.http.post<Measurement>(`${this.api}/measurements`, data);
  }

  deleteMeasurement(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/measurements/${id}`);
  }
}
