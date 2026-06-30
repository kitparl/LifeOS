import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { CalendarService } from './calendar.service';

describe('CalendarService', () => {
  let service: CalendarService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(CalendarService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should create an event', () => {
    service.create({ title: 'Meet', starts_at: new Date().toISOString() }).subscribe((e) => {
      expect(e.title).toBe('Meet');
    });
    const req = http.expectOne(`${environment.apiUrl}/calendar/events`);
    expect(req.request.method).toBe('POST');
    req.flush({
      id: '1',
      title: 'Meet',
      description: null,
      starts_at: new Date().toISOString(),
      ends_at: null,
      all_day: false,
      category: 'personal',
      recurrence: 'none',
      location: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  });
});
