import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { Habit, HabitCreate, HabitListItem, HabitUpdate } from '../models/habit.models';

@Injectable({ providedIn: 'root' })
export class HabitsService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/habits`;

  list(activeOnly = true): Observable<HabitListItem[]> {
    const params = new HttpParams().set('active_only', String(activeOnly));
    return this.http.get<HabitListItem[]>(this.api, { params });
  }

  get(id: string): Observable<Habit> {
    return this.http.get<Habit>(`${this.api}/${id}`);
  }

  create(data: HabitCreate): Observable<Habit> {
    return this.http.post<Habit>(this.api, data);
  }

  update(id: string, data: HabitUpdate): Observable<Habit> {
    return this.http.patch<Habit>(`${this.api}/${id}`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.api}/${id}`);
  }

  completeToday(id: string): Observable<Habit> {
    return this.http.post<Habit>(`${this.api}/${id}/complete`, {});
  }

  uncompleteToday(id: string): Observable<Habit> {
    return this.http.delete<Habit>(`${this.api}/${id}/complete/today`);
  }
}
