import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { CalendarEvent, EventCreate, EventListItem, EventUpdate } from '../models/calendar.models';

@Injectable({ providedIn: 'root' })
export class CalendarService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/calendar/events`;

  list(start?: string, end?: string): Observable<EventListItem[]> {
    let params = new HttpParams();
    if (start) params = params.set('start', start);
    if (end) params = params.set('end', end);
    return this.http.get<EventListItem[]>(this.api, { params });
  }

  get(id: string): Observable<CalendarEvent> {
    return this.http.get<CalendarEvent>(`${this.api}/${id}`);
  }

  create(data: EventCreate): Observable<CalendarEvent> {
    return this.http.post<CalendarEvent>(this.api, data);
  }

  update(id: string, data: EventUpdate): Observable<CalendarEvent> {
    return this.http.patch<CalendarEvent>(`${this.api}/${id}`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }
}
